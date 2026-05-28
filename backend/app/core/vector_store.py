import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from dotenv import load_dotenv

load_dotenv()

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_data")

_chroma_client = None


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


def add_documents(case_id: int, texts: list[str], metadatas: list[dict] = None, ids: list[str] = None):
    from langchain_openai import OpenAIEmbeddings

    collection = get_or_create_collection(case_id)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-v3",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    )

    vectors = embeddings.embed_documents(texts)

    if ids is None:
        import uuid
        ids = [str(uuid.uuid4()) for _ in texts]

    collection.add(
        embeddings=vectors,
        documents=texts,
        metadatas=metadatas or [{}] * len(texts),
        ids=ids,
    )


def search_documents(case_id: int, query: str, k: int = 5) -> list[str]:
    collection = get_or_create_collection(case_id)

    if collection.count() == 0:
        return []

    from langchain_openai import OpenAIEmbeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-v3",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    )

    query_vector = embeddings.embed_query(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(k, collection.count()),
    )

    if results["documents"] and results["documents"][0]:
        return results["documents"][0]
    return []