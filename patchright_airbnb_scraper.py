import asyncio
import re
import os
import httpx
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime

try:
    from patchright.async_api import async_playwright
    PATCHRIGHT_AVAILABLE = True
except ImportError:
    PATCHRIGHT_AVAILABLE = False

class PatchrightAirbnbScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
        
    async def launch(self):
        if not PATCHRIGHT_AVAILABLE: return
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        
    async def close(self):
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
    
    async def _search_via_firecrawl(self, url: str, region: str, nights: int) -> List[Dict]:
        if not self.firecrawl_key:
            print(f"   [Firecrawl] {region}: Kein Key gefunden.")
            return []
        
        print(f"   [Firecrawl] Request an API für {region}...")
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {self.firecrawl_key}", "Content-Type": "application/json"},
                    json={"url": url, "formats": ["html"], "waitFor": 3000}
                )
                print(f"   [Firecrawl] Status für {region}: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    html = data.get('data', {}).get('html', '')
                    print(f"   [Firecrawl] HTML erhalten ({len(html)} bytes)")
                    deals = self._parse_content(html, region, nights)
                    print(f"   [Firecrawl] {len(deals)} Deals extrahiert.")
                    return deals
                else:
                    print(f"   [Firecrawl] API Fehler: {response.text}")
        except Exception as e:
            print(f"   [Firecrawl] Exception: {e}")
        return []

    async def search_airbnb(self, region: str, checkin: str, checkout: str, adults: int = 4) -> List[Dict]:
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = max(1, (d2 - d1).days)
        url = f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}"

        # Patchright Versuch
        deals = await self._run_patchright(url, region, nights)
        if not deals:
            print(f"   [Hybrid] Airbnb Patchright leer für {region}. Nutze Firecrawl...")
            deals = await self._search_via_firecrawl(url, region, nights)
        return deals

    async def _run_patchright(self, url: str, region: str, nights: int) -> List[Dict]:
        if not PATCHRIGHT_AVAILABLE: return []
        try:
            if not self.browser: await self.launch()
            context = await self.browser.new_context(viewport={'width': 1280, 'height': 800}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            page = await context.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=40000)
            try: await page.wait_for_selector('[data-testid="card-container"]', timeout=10000)
            except: pass
            content = await page.content()
            deals = self._parse_content(content, region, nights)
            await context.close()
            return deals
        except Exception as e:
            print(f"   [Patchright] Fehler {region}: {e}")
            return []

    def _parse_content(self, html: str, region: str, nights: int) -> List[Dict]:
        deals = []
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('div', {'data-testid': 'card-container'})
        if not cards:
            # Fallback Selektor
            cards = soup.find_all('div', class_=re.compile(r'property-card|listing-card'))
            
        for card in cards:
            try:
                name_elem = card.find('div', {'data-testid': 'listing-card-title'}) or card.find('h3')
                name = name_elem.get_text(strip=True) if name_elem else "Airbnb"
                card_text = card.get_text(separator=' ')
                prices = [int(p.replace('.', '').replace(',', '')) for p in re.findall(r'€\s*([\d\.,]+)', card_text)]
                price_per_night = 0
                if prices:
                    max_val = max(prices)
                    price_per_night = round(max_val / nights) if max_val > 250 else max_val
                if price_per_night <= 0: continue
                
                image_url = ""
                for img in card.find_all('img'):
                    src = img.get('src', '') or img.get('data-src', '')
                    if '/im/pictures/' in src:
                        image_url = src.split('?')[0] + "?im_w=720"
                        break
                
                link = card.find('a', href=True)
                url = ""
                if link and '/rooms/' in link['href']:
                    room_id = re.search(r'/rooms/(\d+)', link['href'])
                    if room_id: url = f"https://www.airbnb.com/rooms/{room_id.group(1)}"
                
                if not url: continue
                deals.append({"name": name, "location": region, "price_per_night": price_per_night, "rating": 4.8, "reviews": 12, "pet_friendly": True, "source": "airbnb (hybrid)", "url": url, "image_url": image_url})
            except Exception: continue
        return deals

SmartAirbnbScraper = PatchrightAirbnbScraper
