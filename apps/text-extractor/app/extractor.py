import io
import logging
from typing import Dict, Optional

import httpx
import pdfplumber
from bs4 import BeautifulSoup

from oxylabs_scraper import OxylabsScraper

class Extractor:
    def __init__(
        self,
        unpaywall_api_url: str,
        unpaywall_email: str,
        crossref_api_url: str,
        crossref_mailto: str,
        scraper: Optional[OxylabsScraper] = None,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.unpaywall_api_url = unpaywall_api_url.rstrip("/")
        self.unpaywall_email = unpaywall_email
        self.crossref_api_url = crossref_api_url.rstrip("/")
        self.crossref_mailto = crossref_mailto

        self._client = httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0 Safari/537.36"
                )
            },
        )

        self.scraper = scraper

    async def resolve_oa_urls(self, doi: str) -> Dict[str, Optional[str]]:
        url = f"{self.unpaywall_api_url}/{doi}"
        resp = await self._client.get(url, params={"email": self.unpaywall_email})
        resp.raise_for_status()
        data = resp.json()
        best = data.get("best_oa_location") or {}
        pdf_url = best.get("url_for_pdf")
        html_url = best.get("url")

        if pdf_url or html_url:
            return {"pdf": pdf_url, "html": html_url}

        cr_url = f"{self.crossref_api_url}/{doi}"
        resp2 = await self._client.get(cr_url, params={"mailto": self.crossref_mailto})
        resp2.raise_for_status()
        cr_msg = resp2.json().get("message", {})
        for link in cr_msg.get("link", []):
            if link.get("content-type", "").lower() == "application/pdf":
                return {"pdf": link.get("URL"), "html": None}
        return {"pdf": None, "html": None}

    async def extract_pdf_text(self, pdf_bytes: bytes) -> str:
        text_chunks = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_chunks.append(text)
        return "\n".join(text_chunks)

    async def extract_html_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator="\n", strip=True)

    async def get_text_for_doi(self, doi: str) -> str:
        urls = await self.resolve_oa_urls(doi)

        if urls.get("pdf"):
            self.logger.debug("Downloading PDF for DOI %s → %s", doi, urls["pdf"])
            try:
                resp = await self._client.get(urls["pdf"])
                resp.raise_for_status()
                return await self.extract_pdf_text(resp.content)
            except httpx.HTTPStatusError as pdf_err:
                self.logger.warning(
                    "PDF download failed (%s), fallback to HTML", pdf_err
                )

        if urls.get("html"):
            self.logger.debug(
                "Downloading HTML for DOI %s → %s", doi, urls["html"]
            )
            try:
                resp = await self._client.get(urls["html"])
                resp.raise_for_status()
                html = resp.text
            except httpx.HTTPStatusError as html_err:
                self.logger.warning(
                    "Direct HTML fetch failed (%s), attempting Oxylabs scraper…",
                    html_err,
                )
                if not self.scraper:
                    raise
                html = await self.scraper.fetch_html(urls["html"])

            return await self.extract_html_text(html)

        raise RuntimeError(f"No open-access URL found for DOI {doi}")
