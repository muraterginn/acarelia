import os

class Settings:
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    UNPAYWALL_API_URL: str = os.getenv("UNPAYWALL_API_URL", "")
    UNPAYWALL_EMAIL: str = os.getenv("UNPAYWALL_EMAIL", "")

    CROSSREF_API_URL: str = os.getenv("CROSSREF_API_URL", "")
    CROSSREF_MAILTO: str = os.getenv("CROSSREF_MAILTO", "")

    INPUT_QUEUE: str = os.getenv("INPUT_QUEUE", "text-extract-requests")
    OUTPUT_QUEUE: str = os.getenv("OUTPUT_QUEUE", "ai-detection-requests")
    OUTPUT_QUEUE_2: str = os.getenv("OUTPUT_QUEUE_2", "plagiarism-detection-requests")
    PREFETCH_COUNT: int = int(os.getenv("PREFETCH_COUNT", "5"))

settings = Settings()
