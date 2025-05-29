import asyncio
import logging
import httpx
from rapidfuzz import fuzz

from common.messaging import RabbitConsumer, RabbitPublisher
from common.job_store import JobStore
from app.config import settings

DOI_RESOLVE_QUEUE    = "doi-resolve-requests"
TEXT_EXTRACT_QUEUE   = "text-extract-requests"

logger = logging.getLogger("doi-resolver")
logging.basicConfig(level=logging.INFO)

job_store = JobStore(settings.REDIS_URL)

def normalize(text: str) -> str:
    return "".join(c.lower() for c in text if c.isalnum() or c.isspace()).strip()


async def resolve_doi_for_article(job_id: str, title: str, author: str) -> tuple[str | None, bool]:
    """ CrossRef üzerinden DOI ve doğrulama bilgisini döner. """
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
        logger.warning(f"[{job_id}] '{title}' → no CrossRef items")
        return None, False

    # Başlık eşiğini geçenleri filtrele
    title_norm = normalize(title)
    passed_title = []
    max_title_sim = 0.0
    for item in items:
        cand = item.get("title", [""])[0]
        sim = fuzz.token_sort_ratio(title_norm, normalize(cand))
        max_title_sim = max(max_title_sim, sim)
        if sim >= settings.TITLE_SIM_THRESHOLD:
            passed_title.append(item)

    if not passed_title:
        logger.info(f"[{job_id}] '{title}' → title sim max={max_title_sim:.1f}% < {settings.TITLE_SIM_THRESHOLD}%")
        return None, False

    # Yazar eşiği
    author_norm = normalize(author)
    for item in passed_title:
        best_sim = 0.0
        for a in item.get("author", []):
            cand_name = f"{a.get('given','')} {a.get('family','')}"
            best_sim = max(best_sim, fuzz.token_sort_ratio(author_norm, normalize(cand_name)))
        if best_sim >= settings.AUTHOR_SIM_THRESHOLD:
            doi = item.get("DOI")
            logger.info(f"[{job_id}] '{title}' → matched (author sim={best_sim:.1f}%) ⇒ DOI={doi}")
            return doi, True

    logger.info(f"[{job_id}] '{title}' → no author sim ≥ {settings.AUTHOR_SIM_THRESHOLD}% (max={best_sim:.1f}%)")
    return None, False


async def detect_open_access(job_id: str, doi: str) -> bool:
    """ Unpaywall API üzerinden is_oa bilgisini döner. """
    url = f"{settings.UNPAYWALL_API_URL}/{doi}"
    params = {"email": settings.UNPAYWALL_EMAIL}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            is_oa = data.get("is_oa", False)
            logger.info(f"[{job_id}] DOI={doi} → is_oa={is_oa}")
            return is_oa
    except Exception as e:
        logger.warning(f"[{job_id}] OA detect failed for DOI={doi}: {e}")
        return False


async def on_message(payload: dict):
    job_id  = payload.get("job_id")
    author  = payload.get("author", "")
    results = payload.get("results", [])
    publisher = RabbitPublisher(settings.RABBITMQ_URL)

    # --- 1) İşleme başlarken status güncelle ---
    await job_store.set_field(job_id, "state", "DOIs resolving.")
    logger.info(f"[{job_id}] status set to 'doi_resolving'")

    enriched = []
    try:
        for rec in results:
            title = rec.get("title", "")
            doi, verified = None, False
            try:
                doi, verified = await resolve_doi_for_article(job_id, title, author)
            except Exception as e:
                logger.error(f"[{job_id}] DOI resolve error for '{title}': {e}")

            open_access = False
            if doi:
                try:
                    open_access = await detect_open_access(job_id, doi)
                except Exception as e:
                    logger.warning(f"[{job_id}] OA detect failed for DOI={doi}: {e}")

            rec.update({
                "doi":         doi,
                "verified":    verified,
                "open_access": open_access
            })
            enriched.append(rec)

        # --- 2) Kuyruğa başarılı gönderme ---
        await publisher.publish(TEXT_EXTRACT_QUEUE, {
            "job_id": job_id,
            "author": author,
            "results": enriched
        })
        logger.info(f"[{job_id}] published to '{TEXT_EXTRACT_QUEUE}'")

        # --- 3) İşlem bitti, status güncelle ---
        await job_store.set_field(job_id, "state", "DOIs resolved.")
        logger.info(f"[{job_id}] status set to 'doi_resolved'")

    except Exception as e:
        # --- 4) Kritik hata ---
        logger.exception(f"[{job_id}] Unexpected error in on_message: {e}")
        await job_store.set_field(job_id, "state", "DOI resolver error.")
        logger.info(f"[{job_id}] status set to 'doi_error'")


async def main():
    consumer = RabbitConsumer(settings.RABBITMQ_URL)
    await consumer.consume(DOI_RESOLVE_QUEUE, on_message, prefetch_count=1)
    logger.info(f"Listening on '{DOI_RESOLVE_QUEUE}' …")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
