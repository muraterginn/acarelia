import os

class Settings:
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    CROSSREF_MAILTO: str = os.getenv("CROSSREF_MAILTO", "")
    CROSSREF_API_URL: str = os.getenv("CROSSREF_API_URL", "")

    WINSTON_API_URL: str = os.getenv("WINSTON_API_URL", "")
    WINSTON_API_KEY: str = os.getenv("WINSTON_API_KEY", "")

settings = Settings()
