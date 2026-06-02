import os
import logging
import chromadb
from chromadb.config import Settings as ChromaSettings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_data")

_chroma_client = None
_embeddings = None


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _chroma_client


def get_embeddings():
    """单例获取 embeddings 实例"""
    global _embeddings
    if _embeddings is None:
        from langchain_openai import OpenAIEmbeddings
        _embeddings = OpenAIEmbeddings(
            model="text-embedding-v3",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
        )
    return _embeddings


def get_or_create_collection(case_id: int):
    client = get_chroma_client()
    collection_name = f"case_{case_id}"
    return client.get_or_create_collection(name=collection_name)


def add_documents(case_id: int, texts: list[str], metadatas: list[dict] = None, ids: list[str] = None):
    """添加文档到向量库"""
    try:
        collection = get_or_create_collection(case_id)
        embeddings = get_embeddings()

        vectors = embeddings.embed_documents(texts)

        # 校验 metadatas 长度
        if metadatas is not None and len(metadatas) != len(texts):
            logger.warning(f"metadatas 长度 ({len(metadatas)}) 与 texts 长度 ({len(texts)}) 不一致，已忽略 metadatas")
            metadatas = None

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in texts]

        collection.add(
            embeddings=vectors,
            documents=texts,
            metadatas=metadatas or [{}] * len(texts),
            ids=ids,
        )
    except Exception as e:
        logger.error(f"添加文档到向量库失败: {e}")
        raise


def search_documents(case_id: int, query: str, k: int = 5) -> list[str]:
    """搜索最相关的文档片段"""
    try:
        collection = get_or_create_collection(case_id)

        if collection.count() == 0:
            return []

        embeddings = get_embeddings()
        query_vector = embeddings.embed_query(query)

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=min(k, collection.count()),
        )

        if results["documents"] and results["documents"][0]:
            return results["documents"][0]
        return []
    except Exception as e:
        logger.error(f"搜索文档失败: {e}")
        return []