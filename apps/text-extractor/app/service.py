import asyncio
import logging
import json
from typing import Any

from common.messaging import RabbitConsumer, RabbitPublisher
from common.job_store import JobStore

from models import Job, Article
from extractor import Extractor

class TextExtractorService:
    def __init__(
        self,
        consumer: RabbitConsumer,
        publisher: RabbitPublisher,
        job_store: JobStore,
        extractor: Extractor,
        input_queue: str,
        output_queue: str,
        output_queue_2: str,
        prefetch_count: int = 1,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.consumer = consumer
        self.publisher = publisher
        self.job_store = job_store
        self.extractor = extractor
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.output_queue_2 = output_queue_2
        self.prefetch_count = prefetch_count

    async def start(self) -> None:
        await self.consumer.connect()
        await self.publisher.connect()
        await self.consumer.consume(
            self.input_queue, self._on_message, prefetch_count=self.prefetch_count
        )
        self.logger.info("TextExtractorService started, waiting for messages…")
        await asyncio.Event().wait()

    async def _on_message(self, payload: dict) -> None:
        try:
            job = Job.parse_obj(payload)
        except Exception as e:
            self.logger.error("Invalid payload: %s", e)
            return

        # mark start
        await self.job_store.set_field(job.job_id, "state", "Extract service started.")
        self.logger.info("➡ Processing job %s", job.job_id)

        for art in job.results:
            if not (art.doi and art.verified and art.open_access):
                continue

            try:
                text = await self.extractor.get_text_for_doi(art.doi)
                art.text = text
                self.logger.info("✔ Extracted text for DOI %s", art.doi)
                self.logger.info(
                    "─── Extracted full text for DOI %s ───\n%s\n────────────────────────────",
                    art.doi,
                    text or "<empty>",
                )
            except Exception as ex:
                self.logger.exception("Error extracting DOI %s: %s", art.doi, ex)

        try:
            #await self.publisher.publish(self.output_queue, job.dict())
            await self.job_store.set_field(job.job_id, "job_data", json.dumps(job.dict()))
            await self.publisher.publish(self.output_queue, {"job_id": job.job_id})
            await self.publisher.publish(self.output_queue_2, {"job_id": job.job_id})
            await self.job_store.set_field(job.job_id, "state", "Extract service successfully finished.")
            self.logger.info("Job %s done, published to %s", job.job_id, self.output_queue)
        except Exception as ex:
            self.logger.exception("Publish failed for job %s: %s", job.job_id, ex)
            await self.job_store.set_field(job.job_id, "state", "Extract service error.")
