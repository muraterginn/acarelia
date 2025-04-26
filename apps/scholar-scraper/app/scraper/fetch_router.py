from .scholarly_scraper import ScholarlyScraper
from .playwright_scraper import PlaywrightScraper

async def fetch_publications(author_name: str):
    try:
        return await ScholarlyScraper().fetch_publications(author_name)
    except Exception as e:
        print(f"[INFO] ScholarlyScraper failed: {e}")
        return await PlaywrightScraper().fetch_publications(author_name)
