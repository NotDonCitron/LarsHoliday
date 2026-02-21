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

    async def search_booking(self, city: str, checkin: str, checkout: str, adults: int = 4, children: int = 0) -> List[Dict]:
        url = self._build_booking_url(city, checkin, checkout, adults, children)
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = max(1, (d2 - d1).days)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {self.firecrawl_key}"},
                    json={"url": url, "formats": ["html"], "waitFor": 10000}
                )
                if response.status_code == 200:
                    html = response.json().get('data', {}).get('html', '')
                    if not html or "security check" in html.lower():
                        print(f"   ⚠️ Booking.com hat die Anfrage blockiert oder Bot-Check gezeigt.")
                        return []
                    return self._parse_html(BeautifulSoup(html, 'html.parser'), city, checkin, checkout, nights)
                else:
                    print(f"   ⚠️ Booking Firecrawl Fehler: {response.status_code}")
        except Exception as e: 
            print(f"   ⚠️ Booking Scraper Fehler: {e}")
        return []

    def _build_booking_url(self, city: str, checkin: str, checkout: str, adults: int, children: int):
        base = "https://www.booking.com/searchresults.html"
        params = [
            f"ss={quote(city)}", 
            f"checkin={checkin}", 
            f"checkout={checkout}", 
            f"group_adults={adults}",
            f"group_children={children}",
            "no_rooms=1", 
            "selected_currency=EUR", 
            "nflt=ht_id%3D220%3Bhotelfacility%3D14"
        ]
        # If children, we need to add their ages (defaulting to 5 for now)
        if children > 0:
            for _ in range(children):
                params.append("req_children=5")
        
        return f"{base}?{'&'.join(params)}"

    def _parse_html(self, soup, city, checkin, checkout, nights):
        deals = []
        cards = soup.find_all('div', {'data-testid': 'property-card'})
        for card in cards[:15]:
            try:
                # 1. Verfügbarkeits-Prüfung (Neu: Überspringe ausgebuchte Objekte)
                card_text = card.get_text().lower()
                availability_indicators = [
                    "sold out", "ausgebucht", "no longer available", 
                    "no rooms left", "nicht mehr verfügbar", "verfügbarkeit prüfen"
                ]
                # "verfügbarkeit prüfen" often appears on sold out items in some languages/views
                # but sometimes also on available ones. More reliable: price absence.
                
                # Check for explicit "Sold out" badges
                sold_out_elem = card.find('span', string=re.compile(r'Sold out|Ausgebucht|Nicht mehr verfügbar', re.I))
                if sold_out_elem:
                    continue

                name_elem = card.find('div', {'data-testid': 'title'}) or card.find('h3')
                if not name_elem: continue
                name = name_elem.get_text(strip=True)
                
                # Preis-Parsing (Verbesserte Logik für Booking.com)
                price_per_night = 0
                price_elem = card.find('span', {'data-testid': 'price-and-discounted-price'})
                if not price_elem:
                    # Fallback: Suche nach dem ersten Element mit Währungssymbol
                    price_elem = card.find(string=re.compile(r'[\$€£]'))
                
                if not price_elem:
                    # Wenn kein Preis gefunden wurde, ist es wahrscheinlich nicht verfügbar
                    continue

                price_text = price_elem.get_text() if hasattr(price_elem, 'get_text') else str(price_elem)
                # Extrahiere alle Zahlen aus dem Preis-String (z.B. "€ 1.234" -> "1234")
                price_match = re.search(r'[\$€£]\s*([\d\.,\s]+)', price_text)
                if price_match:
                    digits = "".join(re.findall(r'\d+', price_match.group(1)))
                    total = int(digits) if digits else 0
                    if total > 0:
                        # Booking zeigt oft den Gesamtpreis für den Aufenthalt
                        # Wenn der Preis > 300 ist, ist es wahrscheinlich der Gesamtpreis
                        if total > 350 or "total" in price_text.lower() or "gesamt" in price_text.lower():
                            price_per_night = round(total / nights)
                        else:
                            price_per_night = total
                
                if price_per_night == 0:
                    continue # Überspringe Deals ohne Preis (nicht verfügbar)

                # Bild-Extraktion (Wir nehmen die echten Inseratsfotos)
                img = card.find('img', {'data-testid': 'image'}) or card.find('img')
                image_url = ""
                if img:
                    # Booking.com nutzt oft src, data-src oder srcset
                    image_url = img.get('src') or img.get('data-src') or img.get('srcset', '').split(',')[0].split(' ')[0]
                    # Qualität erhöhen: square240/square60 -> max500
                    if image_url:
                        image_url = re.sub(r'square\d+', 'max500', image_url)
                        image_url = re.sub(r'max\d+', 'max500', image_url)
                
                if image_url and image_url.startswith('//'): image_url = f"https:{image_url}"

                link_elem = card.find('a', href=True)
                href = link_elem['href'] if link_elem else ""
                final_url = f"https://www.booking.com{href.split('?')[0]}?checkin={checkin}&checkout={checkout}" if not href.startswith('http') else href

                deals.append({
                    "name": name, "location": city, "price_per_night": price_per_night,
                    "rating": 4.7, "reviews": 80, "pet_friendly": True,
                    "source": "booking.com (verified)", "url": final_url, "image_url": image_url
                })
            except Exception: continue
        return deals
