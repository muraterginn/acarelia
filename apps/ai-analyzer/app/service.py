import json
import logging
import asyncio
import httpx

from typing import Any, Dict
from common.job_store import JobStore
from common.messaging import RabbitConsumer
from app.config import settings

logger = logging.getLogger("ai_analyzer.service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
logger.addHandler(handler)

class AiAnalyzerService:
    def __init__(self, rabbitmq_url: str, redis_url: str, writer_api_key: str, writer_api_url: str):
        self.consumer = RabbitConsumer(rabbitmq_url)
        self.job_store = JobStore(redis_url)

        self.writer_api_key = writer_api_key
        self.writer_api_url = writer_api_url

    async def start(self) -> None:
        logger.info("AiAnalyzerService is starting...")
        await self.consumer.connect()
        await self.consumer.consume(
            queue_name="ai-detection-requests",
            on_message=self.handle_message,
            prefetch_count=1
        )
        logger.info("AiAnalyzerService is now listening to 'ai-detection-requests' queue.")

    async def handle_message(self, payload: Dict[str, Any]) -> None:
        try:
            job_id = payload.get("job_id")
            if not job_id:
                logger.error("Payload does not contain 'job_id': %r", payload)
                return

            logger.info("New job received, job_id=%s", job_id)
            await self.job_store.set_field(job_id, "ai_analyze_status", "AI analyzer started.")
            await self.process_job(job_id)
            await self.job_store.set_field(job_id, "ai_analyze_status", "AI analyzer finished successfully.")
            await self.job_store.set_field(job_id, "plagiarism_check_status", "Plagiarism checker finished successfully.") # Deneme için koydun, sonradan yorum satırına al.
            logger.info("Job %s processed successfully.", job_id)

        except Exception as exc:
            logger.exception("Error while processing job (job_id=%s): %s", payload.get("job_id"), exc)
            await self.job_store.set_field(job_id, "ai_analyze_status", "AI analyzer error.")

    async def process_job(self, job_id: str) -> None:
        raw_job_data = await self.job_store.get_field(job_id, "job_data")
        if raw_job_data is None:
            logger.error("'job:%s:job_data' not found in Redis!", job_id)
            return

        try:
            job_data = json.loads(raw_job_data)
        except json.JSONDecodeError as e:
            logger.exception("job_data JSON parse error (job_id=%s): %s", job_id, e)
            return

        results = job_data.get("results", [])
        if not isinstance(results, list):
            logger.error("'results' in job_data is not a list! (job_id=%s)", job_id)
            return

        async with httpx.AsyncClient(timeout=30.0) as client:
            for idx, article in enumerate(results):
                text = article.get("text")
                if text is None or (isinstance(text, str) and text.strip() == ""):
                    logger.debug("Article %d has empty/null 'text', skipping.", idx)
                    continue

                payload = {"input": text}
                headers = {
                    "Authorization": f"Bearer {self.writer_api_key}",
                    "Content-Type": "application/json"
                }

                try:
                    response = await client.post(
                        self.writer_api_url,
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    logger.error(
                        "Writer API request failed (job_id=%s, article_index=%d): %s",
                        job_id, idx, exc
                    )
                    continue

                try:
                    result_json = response.json()
                    label = result_json.get("label")
                    score = result_json.get("score")
                except Exception as e:
                    logger.exception(
                        "Error parsing Writer API response (job_id=%s, article_index=%d): %s",
                        job_id, idx, e
                    )
                    continue

                article["ai_analyzer_label"] = label
                article["ai_analyzer_score"] = score
                logger.debug(
                    "Job %s: added label=%r, score=%r for article %d",
                    job_id, label, score, idx
                )

        try:
            updated_raw = json.dumps(job_data)
            await self.job_store.set_field(job_id, "job_data", updated_raw)
            logger.info("Updated job_data written to Redis (job_id=%s).", job_id)
        except Exception as e:
            logger.exception("Failed to write update to Redis (job_id=%s): %s", job_id, e)
            return
