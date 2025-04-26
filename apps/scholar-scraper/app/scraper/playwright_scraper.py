import re
import os
import random
from playwright.async_api import async_playwright
from .base import BaseScholarScraper
from dotenv import load_dotenv

# Decodo Residential Proxy bilgileri

load_dotenv()  # .env’i oku

DECO_USER   = os.getenv("DECO_USER")
DECO_PASS   = os.getenv("DECO_PASS")
DECO_HOST   = "gate.decodo.com"
DECO_PORTS  = list(range(10001, 10011))

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    # … listeyi uzatabilirsin
]

class PlaywrightScraper(BaseScholarScraper):

    async def fetch_publications(self, author_name: str, max_pages: int = 2, lang: str = "en"):
        # 1) Önce doğrudan dene
        pubs = await self._run_scrape(author_name, max_pages, lang, use_proxy=False)
        if pubs:
            return pubs

        # 2) Başarısızsa proxy ile tekrar dene
        print("[INFO] Direct scrape failed — retrying via residential proxy")
        return await self._run_scrape(author_name, max_pages, lang, use_proxy=True)


    async def _run_scrape(self, author_name: str, max_pages: int, lang: str, use_proxy: bool):
        publications = []

        async with async_playwright() as p:
            # launch args
            launch_args = {
                "headless": True,
                "slow_mo":  100
            }

            if use_proxy:
                # Rastgele bir port seç
                port = random.choice(DECO_PORTS)
                print(f"[INFO] Using proxy → {DECO_HOST}:{port}")
                launch_args["proxy"] = {
                    "server":   f"http://{DECO_HOST}:{port}",
                    "username": DECO_USER,
                    "password": DECO_PASS
                }

            browser = await p.chromium.launch(**launch_args)
            page    = await browser.new_page()

            # Rastgele UA ve viewport
            ua = random.choice(USER_AGENTS)
            await page.set_extra_http_headers({
                "User-Agent":      ua,
                "Accept-Language": "en-US,en;q=0.9"
            })
            w,h = random.choice([(1280,800),(1366,768),(1440,900)])
            await page.set_viewport_size({"width": w, "height": h})

            for idx in range(max_pages):
                start = idx * 10
                url   = (
                    f"https://scholar.google.com/scholar?start={start}"
                    f"&q={author_name.replace(' ','+')}&hl={lang}&as_sdt=0,5"
                )
                print(f"[DEBUG] ({'proxy' if use_proxy else 'direct'}) goto {url}")

                # Navigate DOMContentLoaded
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                except Exception:
                    print("[WARN] goto timeout — continuing…")

                # İnsan taklidi: bekle + scroll
                await page.wait_for_timeout(random.uniform(2000,4000))
                try:
                    await page.evaluate("""() => {
                        const d = document.body || document.documentElement;
                        window.scrollBy(0, d.scrollHeight);
                    }""")
                    await page.wait_for_timeout(random.uniform(500,1500))
                    await page.evaluate("""() => {
                        const d = document.body || document.documentElement;
                        window.scrollBy(0, -d.scrollHeight);
                    }""")
                except Exception as e:
                    print(f"[WARN] scroll failed: {e}")

                # CAPTCHA kontrolü
                html = await page.content()
                if "detected unusual traffic" in html.lower():
                    print("[WARNING] blocked by CAPTCHA or rate limit")
                    publications = []
                    break

                # Sonuçları çek
                items = await page.query_selector_all("div.gs_ri")
                print(f"[INFO] Page {idx+1} → {len(items)} results")
                if not items:
                    break

                for it in items:
                    title_el = await it.query_selector("h3.gs_rt")
                    title    = await title_el.inner_text() if title_el else "Unknown"
                    pdf_el   = await it.query_selector("div.gs_or_ggsm a")
                    link     = await pdf_el.get_attribute("href") if pdf_el else None

                    year = None
                    info = await it.query_selector("div.gs_a")
                    if info:
                        txt = await info.inner_text()
                        m   = re.search(r"\b(20\d{2}|19\d{2})\b", txt)
                        if m: year = int(m.group(0))

                    cit = None
                    for a in await it.query_selector_all("div.gs_fl a"):
                        txt = await a.inner_text()
                        if "Cited" in txt or "Alıntı" in txt:
                            mm = re.search(r"\d+", txt)
                            if mm: cit = int(mm.group(0))
                            break

                    publications.append({
                        "title":     title,
                        "year":      year,
                        "link":      link,
                        "citations": cit
                    })

                # Sayfalar arası insani bekleme
                await page.wait_for_timeout(random.uniform(1000,3000))

            await browser.close()

        return publications
