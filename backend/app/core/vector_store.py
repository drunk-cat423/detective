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
def rerank_documents(query: str, documents: List[str], top_k: int = 5) -> List[str]:
    """使用 SiliconFlow Rerank API 对文档进行重排序"""
    if not documents:
        return documents

    if not SILICONFLOW_API_KEY:
        logger.warning("未配置 SILICONFLOW_API_KEY，跳过重排序")
        return documents[:top_k]

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

            # 根据 index 从原 documents 中取出重排序后的结果
            results = data.get("results", [])
            reranked = []
            for r in results:
                idx = r["index"]
                reranked.append(documents[idx])

            logger.info(f"Rerank API 重排序完成，返回 {len(reranked)} 条")
            return reranked[:top_k]
    except Exception as e:
        logger.error(f"Rerank API 调用失败: {e}")
        return documents[:top_k]


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


def search_documents(case_id: int, query: str, k: int = 5) -> List[str]:
    """搜索最相关的文档片段"""
    try:
        collection = get_or_create_collection(case_id)
        if collection.count() == 0:
            return []

        # 生成查询向量
        query_vector = embed_query(query)

        # 检索
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=min(k, collection.count()),
        )

        if not results["documents"] or not results["documents"][0]:
            return []
        documents = results["documents"][0]

        # 使用 API 重排序
        return rerank_documents(query, documents, top_k=k)


    except Exception as e:
        logger.error(f"搜索文档失败: {e}")
        return []