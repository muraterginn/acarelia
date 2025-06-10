import asyncio
import logging
import httpx
from datetime import datetime
from rapidfuzz import fuzz

from common.messaging import RabbitConsumer, RabbitPublisher
from common.job_store   import JobStore
from app.config         import settings

DOI_RESOLVE_QUEUE  = "doi-resolve-requests"
TEXT_EXTRACT_QUEUE = "text-extract-requests"

logger = logging.getLogger("doi-resolver")

class DoiResolverService:
    def __init__(self):
        self.consumer  = RabbitConsumer(settings.RABBITMQ_URL)
        self.publisher = RabbitPublisher(settings.RABBITMQ_URL)
        self.job_store     = JobStore(settings.REDIS_URL)

    def normalize(self, text: str) -> str:
        return "".join(c.lower() for c in text if c.isalnum() or c.isspace()).strip()

    async def resolve_doi_for_article(self, job_id: str, title: str, author: str) -> tuple[str|None, bool]:
        params = {
            "query.bibliographic": title,
            "query.author":       author,
            "rows":               5,
            "mailto":             settings.CROSSREF_MAILTO
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(settings.CROSSREF_API_URL, params=params)
            resp.raise_for_status()
            items = resp.json().get("message", {}).get("items", [])

        if not items:
            logger.warning(f"[{job_id}] '{title}' no CrossRef items")
            return None, False

        title_norm = self.normalize(title)
        passed, max_sim = [], 0.0
        for item in items:
            cand = item.get("title", [""])[0]
            sim  = fuzz.token_sort_ratio(title_norm, self.normalize(cand))
            max_sim = max(max_sim, sim)
            if sim >= settings.TITLE_SIM_THRESHOLD:
                passed.append(item)

        if not passed:
            logger.info(f"[{job_id}] '{title}' title sim max={max_sim:.1f}% < {settings.TITLE_SIM_THRESHOLD}%")
            return None, False

        author_norm = self.normalize(author)
        for item in passed:
            best_sim = 0.0
            for a in item.get("author", []):
                name = f"{a.get('given','')} {a.get('family','')}"
                best_sim = max(best_sim, fuzz.token_sort_ratio(author_norm, self.normalize(name)))
            if best_sim >= settings.AUTHOR_SIM_THRESHOLD:
                doi = item.get("DOI")
                logger.info(f"[{job_id}] '{title}' matched (author sim={best_sim:.1f}%) ⇒ DOI={doi}")
                return doi, True

        logger.info(f"[{job_id}] '{title}' no author sim ≥ {settings.AUTHOR_SIM_THRESHOLD}% (max={best_sim:.1f}%)")
        return None, False

    async def detect_open_access(self, job_id: str, doi: str) -> bool:
        url    = f"{settings.UNPAYWALL_API_URL}/{doi}"
        params = {"email": settings.UNPAYWALL_EMAIL}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("is_oa", False)
        except:
            return False

    async def fetch_citation_count(self, job_id: str, doi: str) -> int|None:
        url    = f"{settings.CROSSREF_API_URL}/{doi}"
        params = {"mailto": settings.CROSSREF_MAILTO}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("message", {}).get("is-referenced-by-count")
        except:
            return None

    async def on_message(self, payload: dict):
        job_id  = payload.get("job_id")
        author  = payload.get("author", "")
        results = payload.get("results", [])

        now_str = datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
        await self.job_store.set_field(job_id, "doi_resolver_start_time", now_str)
        await self.job_store.set_field(job_id, "state", "DOIs resolving.")
        enriched = []

        try:
            for rec in results:
                title = rec.get("title", "")
                doi, verified = await self.resolve_doi_for_article(job_id, title, author)
                oa = await self.detect_open_access(job_id, doi) if doi else False

                if verified and rec.get("citations") is None and doi:
                    rec["citations"] = await self.fetch_citation_count(job_id, doi)

                rec.update({"doi": doi, "verified": verified, "open_access": oa})
                enriched.append(rec)

            await self.publisher.publish(TEXT_EXTRACT_QUEUE, {
                "job_id": job_id, "author": author, "results": enriched
            })

            now_str = datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
            await self.job_store.set_field(job_id, "doi_resolver_end_time", now_str)
            await self.job_store.set_field(job_id, "state", "DOIs resolved.")
        except Exception:
            await self.job_store.set_field(job_id, "state", "DOI resolver error.")

    async def start(self):
        await self.consumer.consume(DOI_RESOLVE_QUEUE, self.on_message, prefetch_count=1)
        await asyncio.Event().wait()