import io
import logging
import re
from typing import Dict, List, Optional

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
        # Unpaywall primary
        url = f"{self.unpaywall_api_url}/{doi}"
        resp = await self._client.get(url, params={"email": self.unpaywall_email})
        resp.raise_for_status()
        data = resp.json()
        best = data.get("best_oa_location") or {}
        pdf_url = best.get("url_for_pdf")
        html_url = best.get("url")

        if pdf_url:
            return {"pdf": pdf_url, "html": html_url}
        if html_url:
            return {"pdf": None, "html": html_url}

        # Crossref fallback
        cr_url = f"{self.crossref_api_url}/{doi}"
        resp2 = await self._client.get(cr_url, params={"mailto": self.crossref_mailto})
        resp2.raise_for_status()
        cr_msg = resp2.json().get("message", {})
        for link in cr_msg.get("link", []):
            if link.get("content-type", "").lower() == "application/pdf":
                return {"pdf": link.get("URL"), "html": None}

        return {"pdf": None, "html": None}

    async def extract_pdf_text(self, pdf_bytes: bytes) -> str:
        text_chunks: List[str] = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_chunks.append(text)
        raw = "\n".join(text_chunks)
        return self._normalize_text(raw)

    async def _extract_from_landing(self, landing_url: str) -> Optional[str]:
        # Attempt direct landing fetch
        try:
            resp = await self._client.get(landing_url)
            resp.raise_for_status()
            html = resp.text
        except httpx.HTTPStatusError as e:
            self.logger.warning("Landing page fetch failed (%s), trying Oxylabs…", e)
            if not self.scraper:
                return None
            try:
                html = await self.scraper.fetch_html(landing_url)
            except Exception as ex:
                self.logger.warning("Oxylabs landing fetch failed: %s", ex)
                return None

        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().endswith(".pdf"):
                return href
        return None

    async def get_text_for_doi(self, doi: str) -> Optional[str]:
        """
        Resolve PDF/HTML URLs for the given DOI, try to fetch a PDF from each candidate,
        extract and normalize its text, and return it. Logs every step at INFO level.
        """
        # 1) Resolve OA locations
        urls = await self.resolve_oa_urls(doi)
        self.logger.info("Resolved URLs for %s → %r", doi, urls)

        # 2) Build candidate list: direct PDF first, then landing HTML
        candidates: List[str] = []
        if urls.get("pdf"):
            candidates.append(urls["pdf"])
        if urls.get("html"):
            candidates.append(urls["html"])
            # try to scrape PDF link from landing page
            pdf_link = await self._extract_from_landing(urls["html"])
            if pdf_link:
                self.logger.info("Found embedded PDF link on landing for %s → %s", doi, pdf_link)
                candidates.insert(0, pdf_link)

        # Deduplicate while preserving order
        seen = set()
        candidates = [u for u in candidates if u and u not in seen and not seen.add(u)]
        self.logger.info("PDF candidates for %s → %s", doi, candidates)

        # 3) Try each candidate
        for url in candidates:
            self.logger.info("Trying candidate for %s → %s", doi, url)
            try:
                # HEAD to check content-type
                head = await self._client.head(url)
                ctype = head.headers.get("content-type", "").lower()
                self.logger.info("HEAD %s → %d, content-type=%s", url, head.status_code, ctype)

                if "application/pdf" not in ctype and not url.lower().endswith(".pdf"):
                    self.logger.info("Skipping non-PDF candidate %s", url)
                    continue

                # GET the PDF bytes
                resp = await self._client.get(url)
                self.logger.info("GET %s → %d, %d bytes", url, resp.status_code, len(resp.content or b""))
                resp.raise_for_status()

                # Extract text
                text = await self.extract_pdf_text(resp.content)
                if not text:
                    self.logger.info("Empty text extracted from %s, continuing", url)
                    continue

                self.logger.info("✔ Extracted %d chars for DOI %s from %s", len(text), doi, url)
                return text

            except Exception as exc:
                self.logger.info("PDF candidate %s failed: %s", url, exc)

        # 4) If we reach here, all candidates failed
        self.logger.error("❌ All PDF candidates failed for DOI %s", doi)
        return None

    def _normalize_text(self, text: str) -> str:
        # Normalize line breaks
        text = text.replace('\r\n', '\n')
        # Remove page numbers or isolated digits
        text = re.sub(r'(?m)^\s*\d+\s*$', '', text)
        # Collapse multiple empty lines to two
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Merge broken lines within paragraphs
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        # Remove excessive spaces
        text = re.sub(r' {2,}', ' ', text)
        # Strip leading/trailing whitespace
        return text.strip()
