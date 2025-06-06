import os
import re
import random
import asyncio
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv
from .base import BaseScholarScraper

# Load .env from project root\load_dotenv(find_dotenv())

class OxylabsScraper(BaseScholarScraper):
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        geo_countries: list[str] = None
    ):
        self.username = os.getenv("OXY_USERNAME")
        self.password = os.getenv("OXY_PASSWORD")
        if not self.username or not self.password:
            raise RuntimeError("OXY_USERNAME or OXY_PASSWORD env vars are not set")
        self.endpoint = "https://realtime.oxylabs.io/v1/queries"
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.geo_countries = geo_countries or ["US", "DE", "GB", "FR", "CA"]
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                " AppleWebKit/537.36 (KHTML, like Gecko)"
                " Chrome/100.0.4896.127 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://scholar.google.com/"
        }

    async def fetch_publications(
        self,
        author_name: str,
        max_pages: int = 5,
        lang: str = "en"
    ) -> list[dict]:
        publications: list[dict] = []

        async with httpx.AsyncClient(
            auth=(self.username, self.password),
            headers=self.headers,
            timeout=60.0
        ) as client:

            for page_index in range(max_pages):
                start = page_index * 10
                target_url = (
                    f"https://scholar.google.com/scholar?start={start}"
                    f"&q={author_name.replace(' ', '+')}"
                    f"&hl={lang}&as_sdt=0,5"
                )

                retry = 0
                while retry <= self.max_retries:
                    country = self.geo_countries[retry % len(self.geo_countries)]
                    payload = {
                        "url": target_url,
                        "source": "google",
                        "geo_location": country
                    }
                    print(f"[DEBUG] Using geo_location: {country}")

                    await asyncio.sleep(random.uniform(1, 3))
                    print(f"[DEBUG] Scraping page {page_index + 1}, try {retry + 1}: {target_url}")

                    resp = await client.post(self.endpoint, json=payload)
                    resp.raise_for_status()
                    data = resp.json()

                    try:
                        html = data["results"][0]["content"]
                    except (KeyError, IndexError):
                        print("[WARN] No HTML content, breaking page loop.")
                        retry = self.max_retries + 1
                        break

                    lower_html = html.lower()
                    if "recaptcha" in lower_html:
                        retry += 1
                        wait = self.backoff_factor ** retry
                        print(f"[WARN] CAPTCHA detected, retry after {wait:.1f}s...")
                        await asyncio.sleep(wait)
                        continue

                    soup = BeautifulSoup(html, "lxml")
                    items = soup.select("div.gs_ri")

                    if not items:
                        print("[INFO] No items found on this page, ending pagination.")
                        retry = self.max_retries + 1
                        break

                    for it in items:
                        title_el = it.select_one("h3.gs_rt")
                        title = title_el.get_text(strip=True) if title_el else "Unknown"
                        pdf_el = it.select_one("div.gs_or_ggsm a")
                        link = pdf_el["href"] if pdf_el and pdf_el.has_attr("href") else None

                        year = None
                        meta = it.select_one("div.gs_a")
                        if meta:
                            m = re.search(r"\b(20\d{2}|19\d{2})\b", meta.get_text())
                            if m:
                                year = int(m.group(0))

                        citations = None
                        for a in it.select("div.gs_fl a"):
                            txt = a.get_text()
                            if "cited" in txt.lower() or "alıntı" in txt.lower():
                                mm = re.search(r"\d+", txt)
                                if mm:
                                    citations = int(mm.group(0))
                                break

                        publications.append({
                            "title": title,
                            "year": year,
                            "link": link,
                            "citations": citations
                        })

                    break

                if retry > self.max_retries or not items:
                    break

        return publications
