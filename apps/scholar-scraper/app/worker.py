import asyncio
import logging
import json

import redis.asyncio as aioredis
from aio_pika import IncomingMessage

from common.messaging import RabbitPublisher, RabbitConsumer
from common.job_store import JobStore
from app.config import settings
from app.scraper.fetch_router import fetch_publications

logger = logging.getLogger("scholar-scraper")
job_store = JobStore(settings.REDIS_URL)

publisher = RabbitPublisher(settings.RABBITMQ_URL)
consumer  = RabbitConsumer(settings.RABBITMQ_URL)

async def handle_scrape(payload: dict):
    job_id = payload.get("job_id")
    author = payload.get("author")
    if not job_id or not author:
        logger.error("Malformed payload, missing job_id or author")
        return

    logger.info(f"[{job_id}] Scraping started for author '{author}'")
    await job_store.set_field(job_id, "state", "Scraping started.")

    try:
        publications = await fetch_publications(author)
    except Exception as e:
        logger.exception(f"[{job_id}] Scraper error: {e}")
        await job_store.set_field(job_id, "state", "Scraper error.")
        return

    if not publications:
        logger.info(f"[{job_id}] Scraper found no results")
        await job_store.set_field(job_id, "state", "Scraper found no results.")
        return
    else:
        logger.info(f"[{job_id}] Scraper completed successfully ({len(publications)} papers)")
        await job_store.set_field(job_id, "state", "Scraper completed successfully.")

    doi_request = {
        "job_id": job_id,
        "author": author,
        "results": publications
    }

    await publisher.publish("doi-resolve-requests", doi_request)
    logger.info(f"[{job_id}] Published DOI-resolve request")

async def main():
    # start consuming scrape_requests
    await consumer.consume(
        queue_name="scrape_requests",
        on_message=handle_scrape,
        prefetch_count=1
    )
    logger.info("Scholar-scraper worker running, waiting for messages...")
    # keep the worker alive
    await asyncio.Future()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main())