import os
from langchain_openai import OpenAIEmbeddings

os.environ["DASHSCOPE_API_KEY"] = "sk-3c2dc9a133674ff1839247da5c2a1dde"  # 或从环境变量读取
embeddings = OpenAIEmbeddings(
    model="text-embedding-v4",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
)
vec = embeddings.embed_documents(["测试文本"])
print(vec)