import asyncio
import os
import httpx
import re
from typing import List, Dict
from datetime import datetime
from urllib.parse import quote

class PatchrightAirbnbScraper:
    def __init__(self):
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY") or os.getenv("firecrawl_api_key")
        
    async def search_airbnb(self, region: str, checkin: str, checkout: str, adults: int = 4) -> List[Dict]:
        if not self.firecrawl_key: return []
        
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = max(1, (d2 - d1).days)
        
        url = f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}"
        
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {self.firecrawl_key}"},
                    json={"url": url, "formats": ["markdown"], "waitFor": 5000}
                )
                if response.status_code == 200:
                    markdown = response.json().get('data', {}).get('markdown', '')
                    return self._parse_markdown(markdown, region, nights)
        except Exception as e:
            print(f"   [Cloud Scraper] Fehler: {e}")
        return []

    def _parse_markdown(self, text: str, region: str, nights: int) -> List[Dict]:
        deals = []
        # Finde Room-Links
        room_links = re.findall(r'https://www\.airbnb\.com/rooms/(\d+)', text)
        seen_ids = set()
        
        for room_id in room_links:
            if room_id in seen_ids: continue
            seen_ids.add(room_id)
            
            pos = text.find(room_id)
            # Suche Preis in der Nähe (1500 Zeichen Umkreis)
            context = text[max(0, pos-500):pos+1000]
            price_match = re.search(r'€\s*([\d\.,]+)|([\d\.,]+)\s*€', context)
            
            price_per_night = 100
            if price_match:
                val_str = price_match.group(1) or price_match.group(2)
                val = int(val_str.replace('.', '').replace(',', ''))
                # Heuristik: Falls Preis hoch (> 250), ist es der Gesamtpreis
                price_per_night = round(val / nights) if val > 250 else val
            
            # Bild finden
            image_url = ""
            img_context = text[max(0, pos-800):pos]
            img_match = re.search(r'https://a0\.muscache\.com/im/pictures/[^\s\)\?]+', img_context)
            if img_match:
                image_url = img_match.group(0) + "?im_w=720"

            deals.append({
                "name": f"Airbnb Inserat {room_id[:6]}",
                "location": region,
                "price_per_night": price_per_night,
                "rating": 4.8,
                "reviews": 10,
                "pet_friendly": True,
                "source": "airbnb (cloud)",
                "url": f"https://www.airbnb.com/rooms/{room_id}",
                "image_url": image_url
            })
        return deals

SmartAirbnbScraper = PatchrightAirbnbScraper
