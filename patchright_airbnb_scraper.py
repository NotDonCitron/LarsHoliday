import asyncio
import re
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
        self.context = None
        
    async def launch(self):
        if not PATCHRIGHT_AVAILABLE: raise ImportError("patchright not installed")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 800}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
    async def close(self):
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
    
    async def search_airbnb(self, region: str, checkin: str, checkout: str, adults: int = 4) -> List[Dict]:
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = max(1, (d2 - d1).days)

        if not self.browser: await self.launch()
        page = await self.context.new_page()
        url = f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}"
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=40000)
            await page.wait_for_selector('[data-testid="card-container"]', timeout=15000)
            for _ in range(3):
                await page.mouse.wheel(0, 800)
                await asyncio.sleep(1)
            content = await page.content()
            return self._parse_content(content, region, nights)
        except Exception as e:
            print(f"   [Patchright] Error: {e}")
            return []
        finally:
            await page.close()
    
    def _parse_content(self, html: str, region: str, nights: int) -> List[Dict]:
        deals = []
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('div', {'data-testid': 'card-container'})
        for card in cards:
            try:
                name = (card.find('div', {'data-testid': 'listing-card-title'}) or soup.new_tag('div')).get_text(strip=True)
                card_text = card.get_text(separator=' ')
                prices = [int(p.replace('.', '').replace(',', '')) for p in re.findall(r'€\s*([\d\.,]+)', card_text)]
                if not prices: continue
                max_val = max(prices)
                price_per_night = round(max_val / nights) if max_val > 300 else max_val
                
                image_url = ""
                for img in card.find_all('img'):
                    src = img.get('src', '') or img.get('data-src', '')
                    if '/im/pictures/' in src:
                        image_url = src.split('?')[0] + "?im_w=720"
                        break
                
                link = card.find('a', href=True)
                url = f"https://www.airbnb.com{link['href']}".split('?')[0] if link else ""

                deals.append({
                    "name": name, "location": region, "price_per_night": price_per_night,
                    "rating": 4.8, "reviews": 12, "pet_friendly": True,
                    "source": "airbnb (patchright)", "url": url, "image_url": image_url
                })
            except Exception: continue
        return deals
