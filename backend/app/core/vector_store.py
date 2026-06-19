import os
import logging
import uuid
import chromadb
from chromadb.config import Settings as ChromaSettings
from dotenv import load_dotenv
import dashscope
from dashscope import TextEmbedding
from typing import List, Optional
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent.parent.parent.parent / "models" / "bge-reranker-base"

#
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

load_dotenv()

logger = logging.getLogger(__name__)

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_data")

# 配置 DashScope API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

_chroma_client = None
_reranker = None


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


def embed_documents(texts: List[str], dimensions: int = 1024) -> List[List[float]]:
    """
    使用 DashScope text-embedding-v4 批量获取向量
    每次最多处理 10 个文本
    """
    if not texts:
        return []

    # 批量调用，每次最多10条
    all_vectors = []
    for i in range(0, len(texts), 10):
        batch = texts[i:i + 10]
        resp = TextEmbedding.call(
            model="text-embedding-v4",
            input=batch,
            dimensions=dimensions
        )
        if resp.status_code != 200:
            raise Exception(f"Embedding API error: {resp.message}")

        # 提取向量，按输入顺序排列
        embeddings = resp.output['embeddings']
        # 确保排序正确（根据索引）
        embeddings.sort(key=lambda x: x['text_index'])
        batch_vectors = [item['embedding'] for item in embeddings]
        all_vectors.extend(batch_vectors)

    return all_vectors


def embed_query(query: str, dimensions: int = 1024) -> List[float]:
    """为查询文本生成向量"""
    resp = TextEmbedding.call(
        model="text-embedding-v4",
        input=query,
        dimensions=dimensions
    )
    if resp.status_code != 200:
        raise Exception(f"Embedding API error: {resp.message}")
    return resp.output['embeddings'][0]['embedding']

#重排序逻辑
def get_reranker():
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker = CrossEncoder(str(MODEL_PATH))
            logger.info("重排序模型加载成功")
        except Exception as e:
            logger.error(f"重排序模型加载失败:{e}")
            raise
        return _reranker
def preload_reranker():
    """在整个服务启动时先预加载"""
    try:
        get_reranker()
        logger.info("重排序模型预加载完成")
    except Exception as e:
        logger.warning(f"重排序模型预加载失败:{e}")


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

        #如果召回小于等于五条,则不用排序
        if len(documents)<=5:
            return documents[:k*2]

        #使用重排序
        try:
            reranker = get_reranker()
            pairs = [[query,doc] for doc in documents]
            scores = reranker.predict(pairs)

            scored_docs = list(zip(documents,scores))
            scored_docs.sort(key = lambda x :x[1],reverse=True)

            logger.info(f"重排序完成")
            return [doc for doc,score in scored_docs[:k]]
        except Exception as e:
            logger.error(f"重排序失败,返回原始检索内容.错误信息:{e}")


    except Exception as e:
        logger.error(f"搜索文档失败: {e}")
        return []