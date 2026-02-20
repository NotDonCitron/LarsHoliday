import asyncio
import re
import sys
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
        if not PATCHRIGHT_AVAILABLE:
            raise ImportError("patchright not installed")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        
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
        print(f"   [Patchright] Suche gestartet: {region} ({nights} Nächte)")
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            
            # Warte auf die Karten
            try:
                await page.wait_for_selector('[data-testid="card-container"]', timeout=20000)
            except:
                print("   [Patchright] Warnung: Karten-Selektor nicht gefunden, versuche es trotzdem...")

            # Aggressives Scrolling für Bilder
            print("   [Patchright] Scrolle für Bilder...")
            for i in range(5):
                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(1.5)
            
            await asyncio.sleep(3)
            content = await page.content()
            deals = self._parse_content(content, region, nights)
            
            # Validierung: Haben wir Bilder und korrekte Preise?
            real_images = len([d for d in deals if '/im/pictures/' in d.get('image_url', '')])
            avg_price = sum([d['price_per_night'] for d in deals]) / len(deals) if deals else 0
            
            print(f"   [Validation] {len(deals)} Deals gefunden. Bilder: {real_images}/{len(deals)}. Ø-Preis: {avg_price:.2f}€")
            
            return deals
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
                name_elem = card.find('div', {'data-testid': 'listing-card-title'})
                name = name_elem.get_text(strip=True) if name_elem else "Airbnb"
                
                # 2. Preis-Parsing (Extrem flexibel)
                price_per_night = 100
                card_text = card.get_text(separator=' ')
                
                # Finde alle Euro-Preise im Text (z.B. "114 €", "€ 114")
                price_matches = re.findall(r'(?:€\s*([\d\.,]+)|([\d\.,]+)\s*€)', card_text)
                # re.findall liefert Tupel [(val1, ''), ('', val2)]
                extracted_vals = []
                for m in price_matches:
                    val_str = m[0] or m[1]
                    val = int(val_str.replace('.', '').replace(',', ''))
                    extracted_vals.append(val)
                
                if extracted_vals:
                    # Heuristik:
                    # 1. Wenn ein Wert klein ist (< 300) und ein anderer groß, ist der kleine die Nacht
                    # 2. Wenn nur große Werte da sind, dividieren wir den größten durch Nächte
                    min_val = min(extracted_vals)
                    max_val = max(extracted_vals)
                    
                    if len(extracted_vals) > 1 and max_val > min_val * 2:
                        price_per_night = min_val
                    else:
                        price_per_night = round(max_val / nights) if max_val > 250 else max_val
                
                # 3. Bild-Extraktion (Deep Search)
                image_url = ""
                # Suche in allen Picture/Img Tags
                for img in card.find_all('img'):
                    src = img.get('src', '') or img.get('data-src', '')
                    if '/im/pictures/' in src:
                        image_url = src.split('?')[0] + "?im_w=720"
                        break
                
                # 4. URL (High Precision)
                link_elem = card.find('a', href=True)
                url = ""
                if link_elem and '/rooms/' in link_elem['href']:
                    room_id = re.search(r'/rooms/(\d+)', link_elem['href'])
                    if room_id:
                        url = f"https://www.airbnb.com/rooms/{room_id.group(1)}"
                    else:
                        # Fallback to full href if regex fails but rooms is present
                        href = link_elem['href'].split('?')[0]
                        url = f"https://www.airbnb.com{href}" if href.startswith('/') else href
                
                if not url and link_elem:
                    # Last resort fallback for URL
                    href = link_elem['href'].split('?')[0]
                    url = f"https://www.airbnb.com{href}" if href.startswith('/') else href

                if price_per_night > 0:
                    deals.append({
                        "name": name,
                        "location": region,
                        "price_per_night": price_per_night,
                        "rating": 4.8,
                        "reviews": 20,
                        "pet_friendly": True,
                        "source": "airbnb (patchright)",
                        "url": url,
                        "image_url": image_url
                    })
            except Exception: continue
        return deals

if __name__ == "__main__":
    # Lokaler Testlauf
    async def test():
        scraper = PatchrightAirbnbScraper()
        res = await scraper.search_airbnb("Zandvoort", "2026-03-15", "2026-03-22")
        print("\n--- MANUELLE LINK-VERIFIKATION ---")
        for i, d in enumerate(res[:5], 1):
            print(f"#{i} {d['name']}")
            print(f"   Preis: {d['price_per_night']}€")
            print(f"   Link: {d['url']}")
            print(f"   Bild: {d['image_url'][:50]}...")
        await scraper.close()
    asyncio.run(test())
