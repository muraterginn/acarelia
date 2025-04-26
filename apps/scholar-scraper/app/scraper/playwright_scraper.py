import re
from playwright.async_api import async_playwright
from .base import BaseScholarScraper

class PlaywrightScraper(BaseScholarScraper):
    async def fetch_publications(self, author_name: str, max_pages: int = 5, lang: str = "en"):
        publications = []

        async with async_playwright() as p:
            #browser = await p.chromium.launch(headless=True)
            browser = await p.chromium.launch(
                headless=False,      # başlığımsız değil, görünür mod
                slow_mo=100,         # tüm aksiyonlar arasında 100ms gecikme
                devtools=True        # otomatik olarak DevTools’u aç
            )
            page = await browser.new_page()

            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/115.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            })
            await page.set_viewport_size({"width": 1280, "height": 800})

            for page_index in range(max_pages):
                try:
                    start = page_index * 10
                    search_url = (
                        f"https://scholar.google.com/scholar?start={start}"
                        f"&q={author_name.replace(' ', '+')}&hl={lang}&as_sdt=0,5"
                    )
                    print(f"[DEBUG] Visiting: {search_url}")
                    await page.goto(search_url)
                    await page.wait_for_timeout(3000)  # İnsani bekleme

                    # CAPTCHA var mı kontrol et
                    html = await page.content()
                    if "detected unusual traffic" in html.lower():
                        print("[WARNING] CAPTCHA or block detected by Google Scholar.")
                        break

                    results = await page.query_selector_all("div.gs_ri")
                    print(f"[INFO] Page {page_index+1} - Results found: {len(results)}")

                    if not results:
                        break

                    for result in results:
                        title_el = await result.query_selector('h3.gs_rt')
                        title_text = await title_el.inner_text() if title_el else "Unknown"

                        pdf_link = None
                        pdf_el = await result.query_selector('div.gs_or_ggsm a')
                        if pdf_el:
                            pdf_link = await pdf_el.get_attribute('href')

                        year = None
                        snippet = await result.query_selector('div.gs_a')
                        if snippet:
                            snippet_text = await snippet.inner_text()
                            match = re.search(r'\b(20\d{2}|19\d{2})\b', snippet_text)
                            if match:
                                year = int(match.group(0))

                        citation_count = None
                        links = await result.query_selector_all('div.gs_fl a')
                        for link in links:
                            text = await link.inner_text()
                            if "Alıntı" in text or "Cited" in text:
                                match = re.search(r'\d+', text)
                                if match:
                                    citation_count = int(match.group(0))
                                    break

                        publications.append({
                            "title": title_text,
                            "year": year,
                            "link": pdf_link,
                            "citations": citation_count
                        })

                    await page.wait_for_timeout(2000)  # Sayfalar arası bekleme

                except Exception as e:
                    print(f"[ERROR] Failed to scrape page {page_index+1}: {e}")
                    break

            await browser.close()

        return publications
