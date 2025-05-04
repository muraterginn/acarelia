import asyncio
from app.scraper.playwright_scraper import PlaywrightScraper

async def main():
    scraper = PlaywrightScraper()
    author_name = "Tacha Serif"  # Scholar profili olmayan biri
    print(f"Fetching publications for: {author_name}")
    results = await scraper.fetch_publications(author_name, max_pages=3)
    
    print(f"Total publications found: {len(results)}")
    for i, pub in enumerate(results, 1):
        print(f"\\n[{i}] {pub['title']}")
        print(f"   Year: {pub.get('year')}")
        print(f"   Link: {pub.get('link')}")
        print(f"   Citations: {pub.get('citations')}")

if __name__ == "__main__":
    asyncio.run(main())