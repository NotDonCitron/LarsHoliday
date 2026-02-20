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
        # Airbnb links are often structured as [Name](url) or just raw URL
        room_links = re.findall(r'https://www\.airbnb\.com/rooms/(\d+)', text)
        seen_ids = set()
        
        for room_id in room_links:
            if room_id in seen_ids: continue
            seen_ids.add(room_id)
            
            pos = text.find(room_id)
            context = text[max(0, pos-600):pos+600]
            
            # 1. Rating & Reviews
            rating = 4.8
            reviews = 20
            rate_match = re.search(r'([\d\.,]+)\s*star|Rating\s*([\d\.,]+)', context, re.I)
            if rate_match:
                r_val = rate_match.group(1) or rate_match.group(2)
                try: rating = float(r_val.replace(',', '.'))
                except: pass
            
            rev_match = re.search(r'(\d+)\s*reviews|(\d+)\s*Bewertungen', context, re.I)
            if rev_match:
                try: reviews = int(rev_match.group(1) or rev_match.group(2))
                except: pass

            # 2. Name / Titel (Suche nach Fettschrift oder Überschriften vor dem Link)
            name = "[DEBUG: NAME FEHLT]"
            name_match = re.search(r'[\*\#]{2,}\s*([^\*\n\#]{10,60})', context)
            if name_match:
                name = name_match.group(1).strip()
            else:
                # Fallback: Link-Text
                link_text_match = re.search(r'\[([^\]]{10,60})\]\(https://www\.airbnb\.com/rooms/' + room_id, text)
                if link_text_match:
                    name = link_text_match.group(1).strip()

            # 3. Preis-Präzision
            price_per_night = 0
            # Wir suchen nach Preisen im Kontext
            price_candidates = re.findall(r'[\$€£]\s*([\d\.,]+)', context)
            if price_candidates:
                # Wir nehmen den kleinsten Wert als Nachtpreis (oder berechnen ihn aus dem Gesamtpreis)
                numeric_prices = []
                for p in price_candidates:
                    try:
                        val = int("".join(re.findall(r'\d+', p)))
                        if val > 10: numeric_prices.append(val)
                    except: pass
                
                if numeric_prices:
                    # Wenn "total" oder "Gesamt" im Kontext steht, ist der größte Preis vermutlich der Gesamtpreis
                    is_total = any(kw in context.lower() for kw in ["total", "gesamt", "summe"])
                    if is_total:
                        total_val = max(numeric_prices)
                        price_per_night = round(total_val / nights)
                    else:
                        # Sonst nehmen wir den plausibelsten Wert (unter 300)
                        small_prices = [p for p in numeric_prices if p < 500]
                        price_per_night = min(small_prices) if small_prices else min(numeric_prices)
            
            if price_per_night == 0: price_per_night = 0 # Markierung für Debug

            # 4. Bild-URL
            image_url = ""
            img_match = re.search(r'https://a0\.muscache\.com/im/pictures/[^\s\)\?\!]+', context)
            if img_match: image_url = img_match.group(0).split('?')[0] + "?im_w=720"

            deals.append({
                "name": name, "location": region, "price_per_night": price_per_night,
                "rating": rating, "reviews": reviews, "pet_friendly": True,
                "source": "airbnb (cloud)", "url": f"https://www.airbnb.com/rooms/{room_id}",
                "image_url": image_url
            })
        return deals

SmartAirbnbScraper = PatchrightAirbnbScraper
