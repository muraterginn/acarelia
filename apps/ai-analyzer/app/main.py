import asyncio
import logging

from app.config import settings
from app.service import AiAnalyzerService

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    service = AiAnalyzerService(
        rabbitmq_url=settings.RABBITMQ_URL,
        redis_url=settings.REDIS_URL,
        writer_api_key=settings.WRITER_API_KEY,
        writer_api_url=settings.WRITER_API_URL
    )

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(service.start())
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("AiAnalyzerService is stopping (KeyboardInterrupt).")
    finally:
        loop.close()
        logging.info("Event loop closed.")
