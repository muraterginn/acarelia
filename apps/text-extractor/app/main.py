import asyncio
import logging

from common.messaging import RabbitConsumer, RabbitPublisher
from common.state_store import StateStore

from config import settings
from oxylabs_scraper import OxylabsScraper
from extractor import Extractor
from service import TextExtractorService

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    consumer = RabbitConsumer(settings.RABBITMQ_URL)
    publisher = RabbitPublisher(settings.RABBITMQ_URL)
    state_store = StateStore(settings.REDIS_URL)

    oxylabs_scraper = OxylabsScraper(
        max_retries=3,
        backoff_factor=2.0,
    )

    extractor = Extractor(
        unpaywall_api_url=settings.UNPAYWALL_API_URL,
        unpaywall_email=settings.UNPAYWALL_EMAIL,
        crossref_api_url=settings.CROSSREF_API_URL,
        crossref_mailto=settings.CROSSREF_MAILTO,
        scraper= oxylabs_scraper,
    )

    service = TextExtractorService(
        consumer=consumer,
        publisher=publisher,
        state_store=state_store,
        extractor=extractor,
        input_queue=settings.INPUT_QUEUE,
        output_queue=settings.OUTPUT_QUEUE,
        prefetch_count=settings.PREFETCH_COUNT,
    )

    asyncio.run(service.start())
