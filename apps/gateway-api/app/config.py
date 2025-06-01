import os

class Settings:
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")

settings = Settings()
