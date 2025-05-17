from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    RABBITMQ_URL: str
    REDIS_URL: str

    CROSSREF_MAILTO: str
    CROSSREF_API_URL: str

    UNPAYWALL_EMAIL: str
    UNPAYWALL_API_URL: str

    TITLE_SIM_THRESHOLD: float = 60.0
    AUTHOR_SIM_THRESHOLD: float = 75.0

    class Config:
        env_file = str(Path(__file__).resolve().parents[2] / ".env")
        env_file_encoding = "utf-8"

settings = Settings()