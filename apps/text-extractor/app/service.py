import asyncio
import logging
from typing import Any

from common.messaging import RabbitConsumer, RabbitPublisher
from common.state_store import StateStore

from models import Job, Article
from extractor import Extractor

class TextExtractorService:
    def __init__(
        self,
        consumer: RabbitConsumer,
        publisher: RabbitPublisher,
        state_store: StateStore,
        extractor: Extractor,
        input_queue: str,
        output_queue: str,
        prefetch_count: int = 1,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.consumer = consumer
        self.publisher = publisher
        self.state_store = state_store
        self.extractor = extractor
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.prefetch_count = prefetch_count

    async def start(self) -> None:
        await self.consumer.connect()
        await self.publisher.connect()
        await self.consumer.consume(
            self.input_queue, self._on_message, prefetch_count=self.prefetch_count
        )
        self.logger.info("🛠 TextExtractorService started, waiting for messages…")
        # Sonsuz loop, servis kapanmasın
        await asyncio.Event().wait()

    async def _on_message(self, payload: dict) -> None:
        try:
            job = Job.parse_obj(payload)
        except Exception as e:
            self.logger.error("❌ Geçersiz payload: %s", e)
            return

        await self.state_store.set_status(job.job_id, "Extract service started.")
        self.logger.info("➡ Processing job %s", job.job_id)

        for art in job.results:
            if not (art.doi and art.verified and art.open_access):
                continue

            doi = art.doi
            await self.state_store.set_status(job.job_id, f"extracting:{doi}")
            try:
                text = await self.extractor.get_text_for_doi(doi)
                art.text = text
                await self.state_store.set_status(job.job_id, f"extracted:{doi}")
                self.logger.info("✔ Extracted text for DOI %s", doi)
            except Exception as ex:
                self.logger.exception("❌ Error extracting DOI %s: %s", doi, ex)
                await self.state_store.set_status(job.job_id, f"error:{doi}")

        # Tüm sonuçları yayımla
        try:
            await self.publisher.publish(self.output_queue, job.dict())
            await self.state_store.set_status(job.job_id, "Extract service successfully finished.")
            self.logger.info("🎉 Job %s done, published to %s", job.job_id, self.output_queue)
        except Exception as ex:
            self.logger.exception("❌ Publish failed for job %s: %s", job.job_id, ex)
            await self.state_store.set_status(job.job_id, "error")
