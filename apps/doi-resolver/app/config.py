import os

class Settings:
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    CROSSREF_MAILTO: str = os.getenv("CROSSREF_MAILTO", "")
    CROSSREF_API_URL: str = os.getenv("CROSSREF_API_URL", "")

    UNPAYWALL_EMAIL: str = os.getenv("UNPAYWALL_EMAIL", "")
    UNPAYWALL_API_URL: str = os.getenv("UNPAYWALL_API_URL", "")

    TITLE_SIM_THRESHOLD: float = float(os.getenv("TITLE_SIM_THRESHOLD", "60.0"))
    AUTHOR_SIM_THRESHOLD: float = float(os.getenv("AUTHOR_SIM_THRESHOLD", "75.0"))

settings = Settings()
