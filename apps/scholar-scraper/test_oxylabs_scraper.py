import asyncio
import os
from app.scraper.oxylabs_scraper import OxylabsScraper

async def main():
    author_name = "Tacha Serif"
    print(f"Fetching publications for: {author_name}")
    try:
        scraper = OxylabsScraper()
        results = await scraper.fetch_publications(author_name, max_pages=3)
    except Exception as e:
        print(f"[ERROR] Scraper initialization or fetch failed: {e}")
        return

    print(f"Total publications found: {len(results)}")
    for idx, pub in enumerate(results, start=1):
        print(f"\n[{idx}] {pub.get('title')}")
        print(f"    Year:      {pub.get('year')}")
        print(f"    Link:      {pub.get('link')}")
        print(f"    Citations: {pub.get('citations')}")

if __name__ == "__main__":
    asyncio.run(main())
