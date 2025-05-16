import asyncio
import logging
import httpx
from rapidfuzz import fuzz

from common.messaging import RabbitConsumer, RabbitPublisher
from app.config      import settings

DOI_RESOLVE_QUEUE = "doi-resolve-requests"
OA_PUBLISH_QUEUE  = "oa-requests"

logger = logging.getLogger("doi-resolver")
logging.basicConfig(level=logging.INFO)


def normalize(text: str) -> str:
    return "".join(c.lower() for c in text if c.isalnum() or c.isspace()).strip()


async def resolve_doi_for_article(job_id: str, title: str, author: str) -> tuple[str | None, bool]:
    # 1) CrossRef sorgusu
    params = {
        "query.bibliographic": title,
        "query.author": author,
        "rows": 5,
        "mailto": settings.CROSSREF_MAILTO
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(settings.CROSSREF_API_URL, params=params)
        resp.raise_for_status()
        items = resp.json().get("message", {}).get("items", [])

    if not items:
        logger.warning(f"[{job_id}] '{title}' → no CrossRef items returned")
        return None, False

    # 2) Başlık eşiği kontrolü
    title_norm = normalize(title)
    max_title_sim = 0.0
    passed_title = []
    for item in items:
        cand_title = item.get("title", [""])[0]
        sim = fuzz.token_sort_ratio(title_norm, normalize(cand_title))
        max_title_sim = max(max_title_sim, sim)
        if sim >= settings.TITLE_SIM_THRESHOLD:
            passed_title.append(item)

    if not passed_title:
        logger.info(
            f"[{job_id}] '{title}' → max title sim {max_title_sim:.1f} < "
            f"threshold {settings.TITLE_SIM_THRESHOLD}"
        )
        return None, False

    # 3) Yazar eşiği kontrolü
    author_norm = normalize(author)
    max_author_sim = 0.0
    for item in passed_title:
        best_sim = 0.0
        for a in item.get("author", []):
            cand_name = f"{a.get('given','')} {a.get('family','')}"
            sim = fuzz.token_sort_ratio(author_norm, normalize(cand_name))
            best_sim = max(best_sim, sim)
        max_author_sim = max(max_author_sim, best_sim)
        if best_sim >= settings.AUTHOR_SIM_THRESHOLD:
            doi = item.get("DOI")
            logger.info(f"[{job_id}] '{title}' → matched (title {sim:.1f}%, author {best_sim:.1f}%) ⇒ DOI={doi}")
            return doi, True

    logger.info(
        f"[{job_id}] '{title}' → no author sim ≥ {settings.AUTHOR_SIM_THRESHOLD} "
        f"(max {max_author_sim:.1f})"
    )
    return None, False


async def on_message(payload: dict):
    job_id  = payload.get("job_id")
    author  = payload.get("author", "")
    results = payload.get("results", [])
    publisher = RabbitPublisher(settings.RABBITMQ_URL)

    enriched = []
    for rec in results:
        title = rec.get("title", "")
        try:
            doi, verified = await resolve_doi_for_article(job_id, title, author)
        except Exception as e:
            logger.error(f"[{job_id}] ERROR resolving DOI for '{title}': {e}")
            doi, verified = None, False

        rec.update({"doi": doi, "verified": verified})
        enriched.append(rec)

    out = {"job_id": job_id, "author": author, "results": enriched}
    await publisher.publish(OA_PUBLISH_QUEUE, out)
    logger.info(f"[{job_id}] → published to '{OA_PUBLISH_QUEUE}'")


async def main():
    consumer = RabbitConsumer(settings.RABBITMQ_URL)
    await consumer.consume(DOI_RESOLVE_QUEUE, on_message, prefetch_count=1)
    logger.info(f"Listening on '{DOI_RESOLVE_QUEUE}' …")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())