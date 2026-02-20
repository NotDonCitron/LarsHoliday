import asyncio
import re
import os
import httpx
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote

try:
    from patchright.async_api import async_playwright
    PATCHRIGHT_AVAILABLE = True
except ImportError:
    PATCHRIGHT_AVAILABLE = False

class BookingScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY")

    async def launch(self):
        if not PATCHRIGHT_AVAILABLE: return
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 800}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    async def close(self):
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()

    async def search_booking(self, city: str, checkin: str, checkout: str, adults: int = 4) -> List[Dict]:
        url = self._build_booking_url(city, checkin, checkout, adults)
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = max(1, (d2 - d1).days)

        # 1. Patchright Versuch
        deals = await self._run_patchright(url, city, nights, checkin, checkout, adults)
        
        # 2. Firecrawl Fallback
        if not deals:
            print(f"   [Hybrid] Booking Patchright leer für {city}. Nutze Firecrawl...")
            deals = await self._search_via_firecrawl(url, city, nights, checkin, checkout, adults)
        return deals

    async def _run_patchright(self, url, city, nights, checkin, checkout, adults):
        if not PATCHRIGHT_AVAILABLE: return []
        try:
            if not self.browser: await self.launch()
            page = await self.context.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=40000)
            await asyncio.sleep(5)
            content = await page.content()
            deals = self._parse_html(BeautifulSoup(content, 'html.parser'), city, checkin, checkout, adults, nights)
            await page.close()
            return deals
        except Exception as e:
            print(f"   [Patchright Booking] Fehler: {e}")
            return []

    async def _search_via_firecrawl(self, url, city, nights, checkin, checkout, adults):
        if not self.firecrawl_key: return []
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {self.firecrawl_key}"},
                    json={"url": url, "formats": ["html"], "waitFor": 5000}
                )
                if response.status_code == 200:
                    html = response.json().get('data', {}).get('html', '')
                    return self._parse_html(BeautifulSoup(html, 'html.parser'), city, checkin, checkout, adults, nights)
        except Exception as e:
            print(f"   [Firecrawl Booking] Fehler: {e}")
        return []

    def _build_booking_url(self, city, checkin, checkout, adults):
        base = "https://www.booking.com/searchresults.html"
        params = [f"ss={quote(city)}", f"checkin={checkin}", f"checkout={checkout}", f"group_adults={adults}", "no_rooms=1", "nflt=ht_id%3D220;hotelfacility%3D14"]
        return f"{base}?{'&'.join(params)}"

    def _parse_html(self, soup, city, checkin, checkout, adults, nights):
        deals = []
        cards = soup.find_all('div', {'data-testid': 'property-card'})
        for card in cards[:10]:
            try:
                name = (card.find('div', {'data-testid': 'title'}) or card.find('h3')).get_text(strip=True)
                price_elem = card.find('span', {'data-testid': 'price-and-discounted-price'})
                if not price_elem: continue
                price_val = "".join(re.findall(r'\d+', price_elem.get_text().replace('\xa0', '')))
                total = int(price_val) if price_val else 0
                price_per_night = round(total / nights) if total > 0 else 0
                
                link = card.find('a', {'data-testid': 'title-link'})
                final_url = f"https://www.booking.com{link['href'].split('?')[0]}?checkin={checkin}&checkout={checkout}"
                img = card.find('img')
                image_url = img.get('src') or img.get('data-src') or ""

                deals.append({"name": name, "location": city, "price_per_night": price_per_night, "rating": 4.5, "reviews": 50, "pet_friendly": True, "source": "booking.com (hybrid)", "url": final_url, "image_url": image_url})
            except Exception: continue
        return deals
