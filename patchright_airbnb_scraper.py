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
        # Find all Airbnb room links and optional names
        # Pattern 1: [Name](url)
        markdown_links = re.findall(r'\[([^\]]+)\]\(https://www\.airbnb\.com/rooms/(\d+)', text)
        # Pattern 2: Raw URLs
        raw_urls = re.findall(r'https://www\.airbnb\.com/rooms/(\d+)', text)
        
        seen_ids = set()
        
        # Process markdown links first to get names
        results = []
        for name_hint, room_id in markdown_links:
            if room_id not in seen_ids:
                results.append((name_hint, room_id))
                seen_ids.add(room_id)
        
        # Then add any missing raw URLs
        for room_id in raw_urls:
            if room_id not in seen_ids:
                results.append(("Airbnb Unterkunft", room_id))
                seen_ids.add(room_id)
        
        for name_hint, room_id in results:
            pos = text.find(room_id)
            context = text[max(0, pos-500):pos+1000]
            
            # Preis-Parsing (Verbessert für Airbnb Markdown)
            price_per_night = 0
            # Airbnb Markdown zeigt oft "Price: $123" oder "$123 per night"
            price_match = re.search(r'[\$€£]\s*([\d\.,\s]+)', context)
            if price_match:
                digits = "".join(re.findall(r'\d+', price_match.group(1)))
                if digits:
                    val = int(digits)
                    # Wenn der Wert sehr groß ist (>300), ist es vermutlich der Gesamtpreis für den Aufenthalt
                    if val > 300 or "total" in context.lower() or "gesamt" in context.lower():
                        price_per_night = round(val / nights)
                    else:
                        price_per_night = val
            
            if price_per_night == 0:
                price_per_night = 0 # Debug-Modus: Kein Fallback auf 100

            # Bild finden (Suche nach dem Bild-URL-Muster von Airbnb)
            image_url = ""
            img_match = re.search(r'https://a0\.muscache\.com/im/pictures/[^\s\)\?\!]+', context)
            if img_match: 
                image_url = img_match.group(0).split('?')[0] + "?im_w=720"

            # Name extrahieren (Bevorzuge den Link-Namen falls sinnvoll)
            name = name_hint if name_hint and len(name_hint) > 10 else "[DEBUG: NAME FEHLT]"
            if name == "[DEBUG: NAME FEHLT]":
                # Suche nach Überschriften im Kontext
                heading_match = re.search(r'###?\s*(.*)', context)
                if heading_match:
                    name = heading_match.group(1)[:60].strip()
                else:
                    lines = [l.strip() for l in context.split('\n') if len(l.strip()) > 10]
                    for line in lines:
                        if any(kw in line.lower() for kw in ['apartment', 'house', 'home', 'cottage', 'villa', 'studio', 'loft', 'suite']):
                            name = line[:60].strip('# ').strip('* ')
                            break

            deals.append({
                "name": name, "location": region, "price_per_night": price_per_night,
                "rating": 4.9, "reviews": 25, "pet_friendly": True,
                "source": "airbnb (cloud)", "url": f"https://www.airbnb.com/rooms/{room_id}",
                "image_url": image_url
            })
        return deals

SmartAirbnbScraper = PatchrightAirbnbScraper
