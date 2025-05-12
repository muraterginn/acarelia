import asyncio
import logging
import json

import redis.asyncio as aioredis
from aio_pika import IncomingMessage

from common.messaging import RabbitPublisher, RabbitConsumer
from common.state_store import StateStore
from app.config import settings
from app.scraper.fetch_router import fetch_publications

logger = logging.getLogger("scholar-scraper")
store = StateStore(settings.REDIS_URL)

# init RabbitMQ publisher & consumer
publisher = RabbitPublisher(settings.RABBITMQ_URL)
consumer  = RabbitConsumer(settings.RABBITMQ_URL)

async def handle_scrape(payload: dict):
    """
    Callback for messages from 'scrape_requests' queue.
    payload: { "job_id": str, "author": str }
    """
    job_id = payload.get("job_id")
    author = payload.get("author")
    if not job_id or not author:
        logger.error("Malformed payload, missing job_id or author")
        return

    logger.info(f"[{job_id}] Scraping started for author '{author}'")
    await store.set_status(job_id, "Scraping started.")

    try:
        publications = await fetch_publications(author)
    except Exception as e:
        logger.exception(f"[{job_id}] Scraper error: {e}")
        await store.set_status(job_id, "Scraper error.")
        return

    if not publications:
        logger.info(f"[{job_id}] Scraper found no results")
        await store.set_status(job_id, "Scraper found no results.")
        return
    else:
        logger.info(f"[{job_id}] Scraper completed successfully ({len(publications)} papers)")
        await store.set_status(job_id, "Scraper completed successfully.")

    # prepare DOI request payload
    doi_request = {
        "job_id": job_id,
        "author": author,
        "results": publications
    }

    # publish to doi-resolve-requests queue
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