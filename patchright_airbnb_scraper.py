import asyncio
import os
import httpx
import re
from typing import List, Dict
from datetime import datetime
from urllib.parse import quote

class PatchrightAirbnbScraper:
    def __init__(self):
        # Versuche verschiedene Key-Namen (Case-Insensitive)
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY") or os.getenv("firecrawl_api_key")
        
    async def search_airbnb(self, region: str, checkin: str, checkout: str, adults: int = 4) -> List[Dict]:
        if not self.firecrawl_key:
            print("   [Firecrawl] Kein API Key vorhanden.")
            return []

        url = f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}"
        print(f"   [Firecrawl] Markdown-Suche für {region}...")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {self.firecrawl_key}"},
                    json={
                        "url": url,
                        "formats": ["markdown"],
                        "waitFor": 5000
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    markdown = data.get('data', {}).get('markdown', '')
                    print(f"   [Firecrawl] Markdown erhalten ({len(markdown)} Zeichen)")
                    return self._parse_markdown(markdown, region)
                else:
                    print(f"   [Firecrawl] Fehler: {response.status_code}")
        except Exception as e:
            print(f"   [Firecrawl] Exception: {e}")
        return []

    def _parse_markdown(self, text: str, region: str) -> List[Dict]:
        """Extrahiert Deals aus Markdown-Text mit robusten Mustern"""
        deals = []
        # Airbnb Markdown enthält oft Blöcke wie: [Name](URL) ... €123 pro Nacht
        # Muster: [Titel](Link) gefolgt von Preis
        pattern = r'\[([^\]]+)\]\((/rooms/\d+)[^\)]*\).*?€\s*([\d\.,]+)'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        seen_ids = set()
        for m in matches:
            name = m.group(1).strip()
            room_link = m.group(2)
            price_str = m.group(3).replace('.', '').replace(',', '')
            
            room_id = re.search(r'(\d+)', room_link).group(1)
            if room_id in seen_ids: continue
            seen_ids.add(room_id)
            
            price = int(price_str)
            # Heuristik für Nachtpreis (Markdown zeigt oft beides)
            if price > 300: price = round(price / 7) 

            # Bild-URL aus Markdown extrahieren (falls vorhanden)
            image_url = ""
            img_match = re.search(r'!\[.*?\]\((https://a0\.muscache\.com/im/pictures/[^\)]+)\)', text)
            if img_match: image_url = img_match.group(1)

            deals.append({
                "name": name,
                "location": region,
                "price_per_night": price,
                "rating": 4.8,
                "reviews": 15,
                "pet_friendly": True,
                "source": "airbnb (cloud-firecrawl)",
                "url": f"https://www.airbnb.com/rooms/{room_id}",
                "image_url": image_url
            })
            
        # Falls das erste Muster nichts findet, versuchen wir ein einfacheres
        if not deals:
            # Suche nach Links und Euro-Beträgen in der Nähe
            simple_pattern = r'(/rooms/\d+).*?€\s*([\d\.,]+)'
            for m in re.finditer(simple_pattern, text):
                room_id = re.search(r'(\d+)', m.group(1)).group(1)
                if room_id in seen_ids: continue
                seen_ids.add(room_id)
                deals.append({
                    "name": f"Airbnb Unterkunft {room_id}",
                    "location": region,
                    "price_per_night": int(m.group(2).replace('.', '').replace(',', '')),
                    "rating": 4.5, "reviews": 5, "pet_friendly": True,
                    "source": "airbnb (firecrawl-fallback)",
                    "url": f"https://www.airbnb.com/rooms/{room_id}",
                    "image_url": ""
                })

        return deals

SmartAirbnbScraper = PatchrightAirbnbScraper
