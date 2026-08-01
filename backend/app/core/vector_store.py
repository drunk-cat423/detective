import os
import logging
import uuid
import httpx
import chromadb
from chromadb.config import Settings as ChromaSettings
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Optional

load_dotenv(override=True)

logger = logging.getLogger(__name__)

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_data")

# SiliconFlow API 配置
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_MODEL = "BAAI/bge-m3"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"

# ===== 方案 C：子块检索 + 上下文窗口 =====
CHILD_SIZE_THRESHOLD = 500      # 块长度超过它视为"大块"（旧数据），邻居半径降为 0
WINDOW_RADIUS = 1               # 命中块前后各取 1 个邻居
MAX_WINDOW_TOTAL_CHARS = 3000   # 注入 LLM 的窗口总字数上限

_embedding_client = None
_chroma_client = None



def get_embedding_client():
    global _embedding_client
    if _embedding_client is None:
        if not SILICONFLOW_API_KEY:
            raise ValueError("未设置api")
        _embedding_client = OpenAI(
            api_key=SILICONFLOW_API_KEY,
            base_url=SILICONFLOW_BASE_URL
        )
    return _embedding_client


def get_chroma_client():
    
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _chroma_client


def get_or_create_collection(case_id: int):
    client = get_chroma_client()
    collection_name = f"case_{case_id}"
    return client.get_or_create_collection(name=collection_name)


def embed_documents(texts: List[str]) -> List[List[float]]:
    """
    每次最多处理 10 个文本
    """
    if not texts:
        return []

    client = get_embedding_client()

    # 批量调用，每次最多10条
    all_vectors = []
    for i in range(0, len(texts), 10):
        batch = texts[i:i + 10]
        resp = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
        )

        # 按照输入顺序提取向量
        batch_vectors = [item.embedding for item in resp.data]
        all_vectors.extend(batch_vectors)

    return all_vectors


def embed_query(query: str) -> List[float]:
    """为查询文本生成向量"""
    client = get_embedding_client()
    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    return resp.data[0].embedding

# 重排序逻辑 - 调用 SiliconFlow Rerank API
def rerank_documents(query: str, documents: List[str], top_k: int = 5, return_indices: bool = False):
    """使用 SiliconFlow Rerank API 对文档进行重排序。

    return_indices=True 时返回 (重排序文本列表, 各文本在原 documents 中的下标)，
    调用方可用下标反查 metadata（方案 C 建上下文窗口时需要）。
    """
    if not documents:
        return ([], []) if return_indices else documents

    if not SILICONFLOW_API_KEY:
        logger.warning("未配置 SILICONFLOW_API_KEY，跳过重排序")
        top = documents[:top_k]
        return (top, list(range(len(top)))) if return_indices else top

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{SILICONFLOW_BASE_URL}/rerank",
                headers={
                    "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": RERANK_MODEL,
                    "query": query,
                    "documents": documents,
                    "top_n": top_k,
                    "return_documents": True,
                }
            )
            resp.raise_for_status()
            data = resp.json()

            # 根据 index 从原 documents 中取出重排序后的结果（同时保留下标）
            results = data.get("results", [])
            indices = [r["index"] for r in results[:top_k]]
            reranked = [documents[idx] for idx in indices]

            logger.info(f"Rerank API 重排序完成，返回 {len(reranked)} 条")
            if return_indices:
                return (reranked, indices)
            return reranked
    except Exception as e:
        logger.error(f"Rerank API 调用失败: {e}")
        top = documents[:top_k]
        return (top, list(range(len(top)))) if return_indices else top


def add_documents(case_id: int, texts: List[str], metadatas: Optional[List[dict]] = None,
                  ids: Optional[List[str]] = None):
    """添加文档到向量库"""
    try:
        # 过滤空字符串
        texts = [t for t in texts if t and t.strip()]
        if not texts:
            logger.warning("没有有效的文本可添加")
            return

        # 获取或创建 collection
        collection = get_or_create_collection(case_id)

        # 生成向量
        vectors = embed_documents(texts)

        # 校验 metadatas
        if metadatas is not None and len(metadatas) != len(texts):
            logger.warning(f"metadatas 长度 ({len(metadatas)}) 与 texts 长度 ({len(texts)}) 不一致，已忽略 metadatas")
            metadatas = None

        # 生成 ids
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]

        # 存入 Chroma
        collection.add(
            embeddings=vectors,
            documents=texts,
            metadatas=metadatas or [{}] * len(texts),
            ids=ids,
        )
        logger.info(f"成功添加 {len(texts)} 个文档块到案件 {case_id}")
    except Exception as e:
        logger.error(f"添加文档到向量库失败: {e}")
        raise


def _fetch_sorted_chunks(collection, filename: str):
    """取同一文件的全部块，按 chunk_index 排序。

    Chroma 的 get() 返回顺序不保证与 chunk_index 一致，
    必须显式排序后才能按"index ± 半径"定位前后邻居。
    """
    data = collection.get(where={"filename": filename}, include=["documents", "metadatas"])
    docs = data.get("documents") or []
    metas = data.get("metadatas") or []
    if not docs:
        return []
    return sorted(zip(docs, metas), key=lambda x: int(x[1]["chunk_index"]))


def _build_windows(collection, hit_pairs, radius: int = WINDOW_RADIUS,
                   max_total_chars: int = MAX_WINDOW_TOTAL_CHARS) -> List[str]:
    """按命中块构建上下文窗口。

    hit_pairs: [(命中块文本, 命中块metadata)]。
    - 相邻命中归并成一个窗口，避免重复（坑 3）；
    - 旧数据大块（chunk_len 大）半径降为 0，避免窗口过大（坑 6）；
    - 总字数超过上限时截断（坑 4）。
    """
    by_file = {}
    for doc, meta in hit_pairs:
        fn = (meta or {}).get("filename")
        by_file.setdefault(fn, []).append((doc, meta))

    windows = []
    for fn, pairs in by_file.items():
        # 无 filename 元数据的老数据：命中块单独成窗，不做邻居拼接
        if not fn:
            windows.extend(doc for doc, _ in pairs)
            continue

        items = _fetch_sorted_chunks(collection, fn)
        if not items:
            windows.extend(doc for doc, _ in pairs)
            continue

        index_of = {int(m["chunk_index"]): (doc, m) for doc, m in items}
        hit_indices = sorted(
            int(m["chunk_index"])
            for _, m in pairs
            if m is not None and m.get("chunk_index") is not None
        )
        if not hit_indices:
            windows.extend(doc for doc, _ in pairs)
            continue

        # 合并相邻命中：连续下标归并成一组（坑 3）
        groups = []
        for idx in hit_indices:
            if groups and idx - groups[-1][-1] == 1:
                groups[-1].append(idx)
            else:
                groups.append([idx])

        for group in groups:
            lo, hi = group[0], group[-1]
            # 坑 6：块很大（旧数据 1200 字）时半径降为 0，退化成单块
            group_len = max(
                max(len(index_of[i][0]), int(index_of[i][1].get("chunk_len", 0)))
                for i in group
            )
            r = 0 if group_len > CHILD_SIZE_THRESHOLD else radius
            start = max(0, lo - r)
            end = min(len(items) - 1, hi + r)
            windows.append("\n".join(index_of[i][0] for i in range(start, end + 1)))

    # 坑 4：总字数上限截断，防止上下文膨胀
    if max_total_chars:
        result, total = [], 0
        for w in windows:
            if total + len(w) > max_total_chars:
                remain = max_total_chars - total
                if remain > 0:
                    result.append(w[:remain])
                break
            result.append(w)
            total += len(w)
        return result
    return windows


def search_documents(case_id: int, query: str, k: int = 5) -> List[str]:
    """检索文档（方案 C：子块检索 + 上下文窗口）。

    ① 子块层粗召回 2k 候选（信号聚焦，保证召回率）；
    ② 子块层 Cross-Encoder 重排取 top-k，并保留下标以便反查 metadata；
    ③ 按命中块的前后邻居构建上下文窗口，返回给 LLM（上下文完整）。
    """
    try:
        collection = get_or_create_collection(case_id)
        if collection.count() == 0:
            return []

        query_vector = embed_query(query)

        # ① 子块层粗召回 2k 候选
        recall_count = min(2 * k, collection.count())
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=recall_count,
        )
        if not results.get("documents") or not results["documents"][0]:
            return []
        docs = results["documents"][0]
        raw_metas = results.get("metadatas")
        metas = raw_metas[0] if raw_metas and raw_metas[0] else [{}] * len(docs)

        # ② 子块层重排，取 top-k 命中及其在原列表中的下标
        _, top_indices = rerank_documents(query, docs, top_k=k, return_indices=True)
        if not top_indices:
            return []

        # ③ 按命中块建上下文窗口
        hit_pairs = [(docs[i], metas[i]) for i in top_indices]
        return _build_windows(collection, hit_pairs)

    except Exception as e:
        logger.error(f"搜索文档失败: {e}")
        return []


def delete_documents_by_metadata(case_id: int, filename: str):
    """按案件 ID 和文件名删除 Chroma 中的文档块"""
    try:
        collection = get_or_create_collection(case_id)
        collection.delete(where={"filename": filename})
        logger.info(f"已删除案件 {case_id} 的文档 {filename}")
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise


def list_documents_by_case(case_id: int) -> list:
    """从 Chroma metadata 中提取文件列表（按 filename 去重）"""
    try:
        collection = get_or_create_collection(case_id)
        if collection.count() == 0:
            return []

        all_data = collection.get(include=["metadatas"])
        seen = set()
        files = []
        for meta in all_data.get("metadatas", []):
            if meta and meta.get("filename"):
                fn = meta["filename"]
                if fn not in seen:
                    seen.add(fn)
                    chunk_count = sum(
                        1 for m in all_data["metadatas"]
                        if m and m.get("filename") == fn
                    )
                    files.append({
                        "filename": fn,
                        "chunk_count": chunk_count,
                    })
        return files
    except Exception as e:
        logger.error(f"列出文档失败: {e}")
        return []


# ========== 记忆存储（memory_store collection） ==========

MEMORY_COLLECTION_NAME = "memory_store"


def get_memory_collection():
    """获取/创建全局记忆 collection"""
    client = get_chroma_client()
    return client.get_or_create_collection(name=MEMORY_COLLECTION_NAME)


def add_memory(case_id: int, memory_type: str, content: str, memory_id: str = None):
    """添加一条记忆到 memory_store"""
    try:
        from datetime import datetime
        collection = get_memory_collection()
        doc_id = memory_id or str(uuid.uuid4())
        collection.add(
            documents=[content],
            metadatas=[{
                "case_id": case_id,
                "memory_type": memory_type,
                "created_at": datetime.now().isoformat(),
            }],
            ids=[doc_id],
        )
        logger.info(f"已添加记忆 {doc_id} (type={memory_type}, case_id={case_id})")
        return doc_id
    except Exception as e:
        logger.error(f"添加记忆失败: {e}")
        raise


def update_memory(memory_id: str, content: str):
    """更新一条记忆的内容（根据 ID）"""
    try:
        collection = get_memory_collection()
        collection.update(
            ids=[memory_id],
            documents=[content],
        )
        logger.info(f"已更新记忆 {memory_id}")
    except Exception as e:
        logger.error(f"更新记忆失败: {e}")
        raise


def get_memory(memory_id: str) -> Optional[str]:
    """根据 ID 获取记忆内容"""
    try:
        collection = get_memory_collection()
        result = collection.get(ids=[memory_id])
        if result["documents"]:
            return result["documents"][0]
        return None
    except Exception as e:
        logger.error(f"获取记忆失败: {e}")
        return None


def search_memories(query: str, case_id: Optional[int] = None, k: int = 5) -> List[str]:
    """检索记忆。
    - case_id=None: 检索全局 + 该案件记忆
    - case_id=-1: 只检索全局记忆
    """
    try:
        collection = get_memory_collection()
        if collection.count() == 0:
            return []

        query_vector = embed_query(query)
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=min(k * 2, collection.count()),
        )

        if not results["documents"] or not results["documents"][0]:
            return []

        # 按 case_id 过滤
        filtered = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            meta_case_id = meta.get("case_id")
            if case_id is None:
                # 全部返回
                filtered.append(doc)
            elif case_id == -1:
                # 只返回全局
                if meta_case_id == -1:
                    filtered.append(doc)
            else:
                # 返回全局 + 该案件
                if meta_case_id == -1 or meta_case_id == case_id:
                    filtered.append(doc)

        return filtered[:k]
    except Exception as e:
        logger.error(f"检索记忆失败: {e}")
        return []