from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    database_url: str
    chroma_db_path: str = "./chroma_db"
    groq_api_key: str = ""
    openai_api_key: str = ""
    llm_provider: str = "groq"
    llm_model: str = "llama3-70b-8192"
    embedding_model: str = "all-MiniLM-L6-v2"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080
    redis_url: str = ""
    cors_origins: str = "http://localhost:3000"
    openai_base_url: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
