import os
import logging
import uuid
import chromadb
from chromadb.config import Settings as ChromaSettings
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Optional
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent.parent.parent.parent / "models" / "bge-reranker-base"

#
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

load_dotenv(override=True)

logger = logging.getLogger(__name__)

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_data")

# 配置  API Key
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_MODEL = "BAAI/bge-m3"

_embedding_client = None


_chroma_client = None
_reranker = None



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