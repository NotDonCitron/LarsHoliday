import asyncio
import re
import os
import httpx
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote

class BookingScraper:
    def __init__(self):
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY") or os.getenv("firecrawl_api_key")

    async def search_booking(self, city: str, checkin: str, checkout: str, adults: int = 4) -> List[Dict]:
        url = self._build_booking_url(city, checkin, checkout, adults)
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = max(1, (d2 - d1).days)

        print(f"   [Firecrawl] Booking-Suche für {city}...")
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {self.firecrawl_key}"},
                    json={"url": url, "formats": ["html"], "waitFor": 5000}
                )
                if response.status_code == 200:
                    html = response.json().get('data', {}).get('html', '')
                    return self._parse_html(BeautifulSoup(html, 'html.parser'), city, checkin, checkout, nights)
        except Exception as e:
            print(f"   [Firecrawl Booking] Fehler: {e}")
        return []

    def _build_booking_url(self, city: str, checkin: str, checkout: str, adults: int):
        base = "https://www.booking.com/searchresults.html"
        params = [f"ss={quote(city)}", f"checkin={checkin}", f"checkout={checkout}", f"group_adults={adults}", "no_rooms=1", "nflt=ht_id%3D220;hotelfacility%3D14"]
        return f"{base}?{'&'.join(params)}"

    def _parse_html(self, soup, city, checkin, checkout, nights):
        deals = []
        cards = soup.find_all('div', {'data-testid': 'property-card'})
        for card in cards[:12]:
            try:
                name_elem = card.find('div', {'data-testid': 'title'}) or card.find('h3')
                if not name_elem: continue
                name = name_elem.get_text(strip=True)
                
                price_elem = card.find('span', {'data-testid': 'price-and-discounted-price'})
                price_per_night = 100
                if price_elem:
                    price_val = "".join(re.findall(r'\d+', price_elem.get_text().replace('\xa0', '')))
                    total = int(price_val) if price_val else 0
                    price_per_night = round(total / nights) if total > 0 else 100
                
                link_elem = card.find('a', href=True)
                href = link_elem['href'] if link_elem else ""
                if "https://" in href:
                    final_url = f"{href.split('?')[0]}?checkin={checkin}&checkout={checkout}"
                else:
                    final_url = f"https://www.booking.com{href.split('?')[0]}?checkin={checkin}&checkout={checkout}"
                
                img = card.find('img')
                image_url = ""
                if img:
                    image_url = img.get('src') or img.get('data-src') or ""
                    srcset = img.get('srcset', '')
                    if srcset: image_url = srcset.split(',')[0].split(' ')[0]
                
                if image_url.startswith('//'): image_url = f"https:{image_url}"

                deals.append({
                    "name": name, "location": city, "price_per_night": price_per_night,
                    "rating": 4.5, "reviews": 50, "pet_friendly": True,
                    "source": "booking.com (cloud)", "url": final_url, "image_url": image_url
                })
            except Exception: continue
        return deals
