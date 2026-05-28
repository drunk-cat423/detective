import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "mysql+aiomysql://root:password@localhost:3306/detective_db")
    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_data")
    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

settings = Settings()