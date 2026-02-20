import asyncio
import re
import os
import httpx
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
        except Exception: pass
        return []

    def _parse_markdown(self, text: str, region: str, nights: int) -> List[Dict]:
        deals = []
        room_links = re.findall(r'https://www\.airbnb\.com/rooms/(\d+)', text)
        seen_ids = set()
        
        for room_id in room_links:
            if room_id in seen_ids: continue
            seen_ids.add(room_id)
            
            pos = text.find(room_id)
            context = text[max(0, pos-1000):pos+1500]
            
            # Preis-Parsing (Erkennt $ und €)
            price_match = re.search(r'[\$€]\s*([\d\.,]+)', context)
            price_per_night = 100
            if price_match:
                digits = "".join(re.findall(r'\d+', price_match.group(1)))
                if digits:
                    val = int(digits)
                    price_per_night = round(val / nights) if val > 300 else val
            
            # Bild finden
            image_url = ""
            img_match = re.search(r'https://a0\.muscache\.com/im/pictures/[^\s\)\?]+', context)
            if img_match: image_url = img_match.group(0) + "?im_w=720"

            # Name extrahieren (Erste Zeile im Kontext, die wie ein Titel aussieht)
            name = "Airbnb Unterkunft"
            lines = [l.strip() for l in context.split('\n') if len(l.strip()) > 5]
            for line in lines:
                if any(kw in line.lower() for x in ['apartment', 'house', 'home', 'cottage', 'villa', 'studio', 'loft', 'suite']):
                    name = line[:50]
                    break

            deals.append({
                "name": name, "location": region, "price_per_night": price_per_night,
                "rating": 4.9, "reviews": 25, "pet_friendly": True,
                "source": "airbnb (cloud)", "url": f"https://www.airbnb.com/rooms/{room_id}",
                "image_url": image_url
            })
        return deals

SmartAirbnbScraper = PatchrightAirbnbScraper
