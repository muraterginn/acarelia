import json
import logging
import re
import aiohttp

from datetime import datetime
from common.job_store import JobStore
from common.messaging import RabbitConsumer
from config import settings

logger = logging.getLogger("plagiarism-checker.service")


class PlagiarismCheckerService:
    def __init__(self):
        self.rabbit_url = settings.RABBITMQ_URL
        self.redis_url = settings.REDIS_URL

        self.crossref_base = settings.CROSSREF_API_URL
        self.crossref_mailto = settings.CROSSREF_MAILTO

        self.winston_url = settings.WINSTON_API_URL
        self.winston_key = settings.WINSTON_API_KEY

        self.job_store = JobStore(self.redis_url)
        self.consumer = RabbitConsumer(self.rabbit_url)

    async def start(self):
        await self.consumer.consume(
            queue_name="plagiarism-detection-requests",
            on_message=self._on_message,
            prefetch_count=1,
        )
        logger.info("PlagiarismCheckerService is now listening on queue 'plagiarism-detection-requests'.")

    async def _on_message(self, payload: dict):
        job_id = payload.get("job_id")
        if not job_id:
            logger.error("Received message without 'job_id': %r", payload)
            return

        try:
            now_str = datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
            await self.job_store.set_field(job_id, "plagiarism_checker_start_time", now_str)
            await self.job_store.set_field(job_id, "plagiarism_check_status", "Plagiarism checker started.")
            raw_job_initial = await self.job_store.get_field(job_id, "job_data")
            if not raw_job_initial:
                logger.error("No job_data found in Redis for job_id=%s", job_id)
                return

            job_data_initial = json.loads(raw_job_initial)
            results_initial = job_data_initial.get("results", [])
            if not isinstance(results_initial, list):
                logger.error("Invalid 'results' format for job_id=%s: %r", job_id, results_initial)
                return

            updated_results = []
            for article in results_initial:
                new_article = article.copy()

                text = new_article.get("text")
                if not text:
                    new_article["plagiarism_checker_results"] = None
                    updated_results.append(new_article)
                    continue

                doi = new_article.get("doi")
                if not doi:
                    new_article["plagiarism_checker_results"] = None
                    updated_results.append(new_article)
                    continue

                crossref_links = await self._fetch_crossref_links(doi)
                if not crossref_links:
                    logger.warning("No Crossref links found for DOI=%s; proceeding with empty excluded_sources.", doi)

                snippet = self._extract_snippet(text, word_count=30)
                if not snippet:
                    logger.warning("Could not extract a valid snippet for article DOI=%s; skipping Winston call.", doi)
                    new_article["plagiarism_checker_results"] = None
                    updated_results.append(new_article)
                    continue

                try:
                    winston_result = await self._call_winston(snippet, excluded_sources=crossref_links)
                    new_article["plagiarism_checker_results"] = winston_result
                except Exception as e:
                    logger.exception("Error while calling Winston API for DOI=%s: %s", doi, e)
                    new_article["plagiarism_checker_results"] = None

                updated_results.append(new_article)

            raw_job_latest = await self.job_store.get_field(job_id, "job_data")
            if not raw_job_latest:
                logger.error("No job_data found in Redis when trying to merge for job_id=%s", job_id)
                return

            job_data_latest = json.loads(raw_job_latest)
            results_latest = job_data_latest.get("results", [])
            if not isinstance(results_latest, list):
                logger.error("Invalid 'results' format on latest fetch for job_id=%s: %r", job_id, results_latest)
                return

            merged_results = []
            for idx, article_latest in enumerate(results_latest):
                merged = article_latest.copy()

                if idx < len(updated_results):
                    merged["plagiarism_checker_results"] = updated_results[idx].get("plagiarism_checker_results")
                else:
                    merged["plagiarism_checker_results"] = None

                merged_results.append(merged)

            job_data_latest["results"] = merged_results
            now_str = datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
            await self.job_store.set_field(job_id, "plagiarism_checker_end_time", now_str)
            await self.job_store.set_field(job_id, "plagiarism_check_status", "Plagiarism checker finished successfully.")
            await self.job_store.set_field(job_id, "job_data", json.dumps(job_data_latest))
            logger.info("Merged and updated job_data in Redis for job_id=%s", job_id)

        except Exception as e:
            logger.exception("Failure processing job_id=%s: %s", job_id, e)

    async def _fetch_crossref_links(self, doi: str) -> list[str]:
        endpoint = f"{self.crossref_base}/{doi}"
        params = {"mailto": self.crossref_mailto}

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params) as resp:
                if resp.status != 200:
                    logger.warning("Crossref returned %d for DOI=%s", resp.status, doi)
                    return []

                data = await resp.json()
                message = data.get("message", {})
                links = message.get("link", [])
                urls = [item.get("URL") for item in links if item.get("URL")]
                unique_urls = list(dict.fromkeys(urls))
                logger.debug("Crossref links for DOI=%s: %s", doi, unique_urls)
                return unique_urls

    def _extract_snippet(self, text: str, word_count: int = 30) -> str | None:
        cleaned = re.sub(r"\\u[0-9A-Fa-f]{4}", "", text)

        tokens = cleaned.split()
        total = len(tokens)
        if total < word_count:
            snippet_tokens = tokens
        else:
            mid = total // 2
            start = max(0, mid - word_count // 2)
            end = min(total, start + word_count)
            snippet_tokens = tokens[start:end]

        snippet = " ".join(snippet_tokens).strip()
        if "\\u" in snippet:
            snippet = snippet.replace("\\u", "")

        return snippet or None

    async def _call_winston(self, snippet: str, excluded_sources: list[str]) -> dict:
        headers = {
            "Authorization": f"Bearer {self.winston_key}",
            "Content-Type": "application/json",
        }
        body = {
            "text": snippet,
            "excluded_sources": excluded_sources,
            "language": "en",
            "country": "us",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.winston_url, json=body, headers=headers) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Winston API döndü: {resp.status} - {await resp.text()}")
                result = await resp.json()
                return result