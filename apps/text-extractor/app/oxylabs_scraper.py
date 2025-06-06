import os
import random
import asyncio
import logging
from typing import List, Optional

import httpx


class OxylabsScraper:
    """
    Oxylabs Realtime Scraper ile:
    - İnsan davranışını taklit eden gecikmeler
    - CAPTCHA tespiti ve retry
    - Coğrafi lokasyon rotasyonu
    Endpoint: POST https://realtime.oxylabs.io/v1/queries
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        geo_countries: Optional[List[str]] = None,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)

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
                " Chrome/115.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def fetch_html(self, url: str) -> str:
        async with httpx.AsyncClient(
            auth=(self.username, self.password),
            headers=self.headers,
            timeout=60.0,
            follow_redirects=True,
        ) as client:

            for attempt in range(1, self.max_retries + 1):
                geo = self.geo_countries[(attempt - 1) % len(self.geo_countries)]
                payload = {
                    "url": url,
                    "source": "text-extractor",
                    "geo_location": geo,
                }

                await asyncio.sleep(random.uniform(1, 3))
                self.logger.debug(f"[Oxylabs] Attempt {attempt} for {url} (geo={geo})")

                resp = await client.post(self.endpoint, json=payload)
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    self.logger.warning("[Oxylabs] HTTP %s, retrying...", e)
                    await asyncio.sleep(self.backoff_factor ** attempt)
                    continue

                data = resp.json()
                html = data.get("results", [{}])[0].get("content")
                if not html:
                    self.logger.warning("[Oxylabs] Empty content, retrying...")
                    await asyncio.sleep(self.backoff_factor ** attempt)
                    continue

                if "recaptcha" in html.lower():
                    self.logger.warning("[Oxylabs] CAPTCHA detected, retrying...")
                    await asyncio.sleep(self.backoff_factor ** attempt)
                    continue

                return html

        raise RuntimeError(f"Oxylabs failed to fetch HTML for {url}")
