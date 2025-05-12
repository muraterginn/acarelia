from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    RABBITMQ_URL: str
    REDIS_URL: str

    class Config:
        env_file = str(Path(__file__).resolve().parents[2] / ".env")
        env_file_encoding = "utf-8"

settings = Settings()
