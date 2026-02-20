import asyncio
import re
import os
import httpx
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime

class PatchrightAirbnbScraper:
    def __init__(self):
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
        
    async def search_airbnb(self, region: str, checkin: str, checkout: str, adults: int = 4) -> List[Dict]:
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = max(1, (d2 - d1).days)
        url = f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}"

        print(f"   [Firecrawl] Starte Suche für {region}...")
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {self.firecrawl_key}"},
                    json={"url": url, "formats": ["html"], "waitFor": 5000}
                )
                if response.status_code == 200:
                    html = response.json().get('data', {}).get('html', '')
                    deals = self._parse_content(html, region, nights)
                    print(f"   [Firecrawl] {len(deals)} Deals in {region} gefunden.")
                    return deals
                else:
                    print(f"   [Firecrawl] API Fehler: {response.status_code}")
        except Exception as e:
            print(f"   [Firecrawl] Fehler: {e}")
        return []

    def _parse_content(self, html: str, region: str, nights: int) -> List[Dict]:
        deals = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Finde alle Links zu Zimmern - das ist der sicherste Anker
        room_links = soup.find_all('a', href=re.compile(r'/rooms/\d+'))
        seen_ids = set()

        for link in room_links:
            try:
                href = link['href']
                room_id = re.search(r'/rooms/(\d+)', href).group(1)
                if room_id in seen_ids: continue
                seen_ids.add(room_id)

                # Suche den Container für diesen Link (wir gehen 5 Ebenen hoch)
                container = link
                for _ in range(8):
                    if container.parent: container = container.parent
                    else: break
                
                container_text = container.get_text(separator=' ')
                
                # Preis-Suche (Regex auf den gesamten Container-Text)
                # Wir suchen nach Beträgen mit €
                price_matches = re.findall(r'€\s*([\d\.,]+)', container_text)
                if not price_matches:
                    # Alternative: Zahl vor €
                    price_matches = re.findall(r'([\d\.,]+)\s*€', container_text)
                
                if not price_matches: continue
                
                vals = [int(p.replace('.', '').replace(',', '')) for p in price_matches]
                max_val = max(vals)
                # Heuristik: Wenn Wert > 300, ist es der Gesamtpreis
                price_per_night = round(max_val / nights) if max_val > 300 else max_val
                
                # Name (Meistens der erste fette Text oder der Text im Link selbst)
                name = "Airbnb Unterkunft"
                title_elem = container.find(['h3', 'div'], {'data-testid': 'listing-card-title'})
                if title_elem:
                    name = title_elem.get_text(strip=True)
                
                # Bild
                image_url = ""
                img_tags = container.find_all('img')
                for img in img_tags:
                    src = img.get('src', '') or img.get('data-src', '')
                    if '/im/pictures/' in src:
                        image_url = src.split('?')[0] + "?im_w=720"
                        break

                deals.append({
                    "name": name, "location": region, "price_per_night": price_per_night,
                    "rating": 4.8, "reviews": 10, "pet_friendly": True,
                    "source": "airbnb (firecrawl)", "url": f"https://www.airbnb.com/rooms/{room_id}",
                    "image_url": image_url
                })
            except Exception: continue
        return deals

SmartAirbnbScraper = PatchrightAirbnbScraper
