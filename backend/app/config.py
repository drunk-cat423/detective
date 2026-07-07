import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "mysql+aiomysql://root:password@localhost:3306/detective_db")
    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_data")
    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    siliconflow_api_key: str = os.getenv("SILICONFLOW_API_KEY", "")

    # 登录认证配置
    auth_enabled: bool = os.getenv("AUTH_ENABLED", "false").lower() in ("true", "1", "yes")
    auth_password: str = os.getenv("AUTH_PASSWORD", "")
    auth_secret_key: str = os.getenv("AUTH_SECRET_KEY", "change-me-to-a-random-secret-key")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

settings = Settings()