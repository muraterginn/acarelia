from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    RABBITMQ_URL: str
    REDIS_URL: str

    UNPAYWALL_API_URL: str
    UNPAYWALL_EMAIL: str

    CROSSREF_API_URL: str
    CROSSREF_MAILTO: str

    INPUT_QUEUE: str = "text-extract-requests"
    OUTPUT_QUEUE: str = "ai-detection-requests"
    OUTPUT_QUEUE_2: str = "plagiarism-detection-requests"
    PREFETCH_COUNT: int = 5

    class Config:
        case_sensitive = True

settings = Settings()
