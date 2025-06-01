import os

class Settings:
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    WRITER_API_URL: str = os.getenv("WRITER_API_URL", "")
    WRITER_API_KEY: str = os.getenv("WRITER_API_KEY", "")

settings = Settings()
