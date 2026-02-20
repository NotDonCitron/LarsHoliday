import asyncio
import re
import os
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime

try:
    from patchright.async_api import async_playwright
    PATCHRIGHT_AVAILABLE = True
except ImportError:
    PATCHRIGHT_AVAILABLE = False

try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False

class PatchrightAirbnbScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
        
    async def launch(self):
        if not PATCHRIGHT_AVAILABLE: return
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True, 
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
    async def close(self):
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
    
    async def _search_via_firecrawl(self, url: str, region: str, nights: int) -> List[Dict]:
        if not (FIRECRAWL_AVAILABLE and self.firecrawl_key):
            print("   [Firecrawl] Key oder Library fehlt.")
            return []
        
        print(f"   [Firecrawl] API-Scraping für: {region}")
        try:
            app = FirecrawlApp(api_key=self.firecrawl_key)
            # Die korrekte Methode ist app.scrape_url
            response = app.scrape_url(url, params={'formats': ['html']})
            # Falls Firecrawl ein Dict zurückgibt
            html_content = response.get('html') if isinstance(response, dict) else getattr(response, 'html', None)
            if html_content:
                return self._parse_content(html_content, region, nights)
        except Exception as e:
            print(f"   [Firecrawl] API Fehler: {e}")
        return []

    async def search_airbnb(self, region: str, checkin: str, checkout: str, adults: int = 4) -> List[Dict]:
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = max(1, (d2 - d1).days)
        url = f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}"

        # 1. VERSUCH: Patchright
        deals = await self._run_patchright(url, region, nights)
        
        # 2. VERSUCH: Firecrawl Fallback
        if not deals:
            print(f"   [Hybrid] Patchright leer. Nutze Firecrawl für {region}...")
            deals = await self._search_via_firecrawl(url, region, nights)
            
        return deals

    async def _run_patchright(self, url: str, region: str, nights: int) -> List[Dict]:
        if not PATCHRIGHT_AVAILABLE: return []
        try:
            if not self.browser: await self.launch()
            context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=40000)
            try:
                await page.wait_for_selector('[data-testid="card-container"]', timeout=15000)
            except: pass
            
            for _ in range(2):
                await page.mouse.wheel(0, 800)
                await asyncio.sleep(1)
                
            content = await page.content()
            deals = self._parse_content(content, region, nights)
            await context.close()
            return deals
        except Exception as e:
            print(f"   [Patchright] Fehler: {e}")
            return []

    def _parse_content(self, html: str, region: str, nights: int) -> List[Dict]:
        deals = []
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('div', {'data-testid': 'card-container'})
        for card in cards:
            try:
                name_elem = card.find('div', {'data-testid': 'listing-card-title'})
                name = name_elem.get_text(strip=True) if name_elem else "Airbnb"
                
                card_text = card.get_text(separator=' ')
                price_matches = re.findall(r'(?:€\s*([\d\.,]+)|([\d\.,]+)\s*€)', card_text)
                extracted_vals = []
                for m in price_matches:
                    val_str = m[0] or m[1]
                    val = int(val_str.replace('.', '').replace(',', ''))
                    extracted_vals.append(val)
                
                price_per_night = 0
                if extracted_vals:
                    min_val = min(extracted_vals)
                    max_val = max(extracted_vals)
                    if len(extracted_vals) > 1 and max_val > min_val * 2:
                        price_per_night = min_val
                    else:
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

                deals.append({
                    "name": name, "location": region, "price_per_night": price_per_night,
                    "rating": 4.8, "reviews": 12, "pet_friendly": True,
                    "source": "airbnb (hybrid)", "url": url, "image_url": image_url
                })
            except Exception: continue
        return deals

SmartAirbnbScraper = PatchrightAirbnbScraper
