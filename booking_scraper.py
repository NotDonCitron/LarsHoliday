import asyncio
import re
import os
import httpx
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote

# Import bypass utilities
from rate_limit_bypass import (
    smart_requester, 
    get_random_user_agent, 
    generate_user_agent,
    cache,
    RequestDelayer
)

class BookingScraper:
    def __init__(self):
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY") or os.getenv("firecrawl_api_key")
        self.cache = cache
        self.delayer = RequestDelayer(min_delay=5, max_delay=15)

    async def search_booking(self, city: str, checkin: str, checkout: str, adults: int = 4, children: int = 0) -> List[Dict]:
        """
        Smart search with fallback strategies.
        """
        # Specificity fix
        search_city = city
        if "," not in city:
            low_city = city.lower()
            if any(x in low_city for x in ["hamburg", "berlin", "münchen", "munich", "köln", "cologne"]):
                search_city = f"{city}, Germany"
            elif any(x in low_city for x in ["amsterdam", "rotterdam", "utrecht", "zandvoort", "texel", "zeeland"]):
                search_city = f"{city}, Netherlands"

        # Calculate nights
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = max(1, (d2 - d1).days)
        
        strategies = [
            ("curl", self._search_curl),
            ("firecrawl", self._search_firecrawl),
            ("fallback", self._get_fallback_data)
        ]
        
        for name, strategy in strategies:
            try:
                print(f"   [Booking] Trying {name} strategy for {search_city}...")
                deals = await strategy(search_city, checkin, checkout, adults, children, nights)
                if deals and len(deals) > 0:
                    print(f"   ✅ {name} strategy succeeded: {len(deals)} deals")
                    return deals
            except Exception as e:
                print(f"   ❌ {name} strategy failed: {str(e)[:100]}")
                continue
        
        return self._get_fallback_data(search_city, nights)

    async def _search_curl(self, city: str, checkin: str, checkout: str, adults: int, children: int, nights: int) -> List[Dict]:
        """Fast strategy using local httpx request."""
        await self.delayer.wait()
        url = self._build_booking_url(city, checkin, checkout, adults, children)
        
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7", # Prefer German
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                if "security check" in response.text.lower() or "captcha" in response.text.lower():
                    raise Exception("Blocked by Booking.com (Bot Detection)")
                
                soup = BeautifulSoup(response.text, 'html.parser')
                return self._parse_html(soup, city, checkin, checkout, nights)
            else:
                raise Exception(f"HTTP Error {response.status_code}")

    async def _search_firecrawl(self, city: str, checkin: str, checkout: str, adults: int, children: int, nights: int) -> List[Dict]:
        """Verified strategy using Firecrawl cloud scraping with improved extraction."""
        if not self.firecrawl_key:
            raise Exception("Firecrawl API key missing")
            
        url = self._build_booking_url(city, checkin, checkout, adults, children)
        
        async def make_firecrawl_call():
            async with httpx.AsyncClient(timeout=150.0) as client:
                return await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {self.firecrawl_key}"},
                    json={
                        "url": url, 
                        "formats": ["markdown", "html"], 
                        "waitFor": 15000,
                        "actions": [
                            {"type": "scroll", "direction": "down", "amount": 1000},
                            {"type": "wait", "milliseconds": 2000},
                            {"type": "scroll", "direction": "down", "amount": 1000}
                        ]
                    }
                )

        response = await smart_requester.request(make_firecrawl_call)
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            html = data.get('html', '')
            markdown = data.get('markdown', '')
            
            deals = []
            if html and "security check" not in html.lower():
                deals = self._parse_html(BeautifulSoup(html, 'html.parser'), city, checkin, checkout, nights)
            
            # If HTML failed or found nothing, try markdown
            if not deals and markdown:
                print(f"   [Booking] HTML yielded no results, trying markdown fallback...")
                deals = self._parse_markdown(markdown, city, nights)
                
            if not deals:
                raise Exception("Booking blocked or no results found in HTML/Markdown")
                
            return deals
        else:
            raise Exception(f"Firecrawl API Error: {response.status_code}")

    def _parse_markdown(self, markdown: str, city: str, nights: int) -> List[Dict]:
        """Improved markdown parser for Booking.com results."""
        deals = []
        # Pattern for property names in markdown: ### [Name](url)
        # Booking.com sometimes adds "Opens in new window" or similar
        
        # Split into property sections using common markdown markers
        sections = re.split(r'###\s*\[', markdown)
        for section in sections[1:]: # Skip header
            try:
                # Re-add the bracket for matching
                section = '[' + section
                name_match = re.search(r'\[([^\]]+)\]\((https://www\.booking\.com/hotel/[^\)]+)\)', section)
                if not name_match: continue
                
                name = name_match.group(1).replace('\\', '').replace('Opens in new window', '').strip()
                url = name_match.group(2).strip()
                
                # Find all prices in this section
                prices = re.findall(r'€\s*([\d\.,\s]+)', section)
                if not prices: continue
                
                # Clean prices and convert to int
                valid_vals = []
                for p in prices:
                    digits = "".join(re.findall(r'\d+', p))
                    if digits: valid_vals.append(int(digits))
                
                if not valid_vals: continue
                
                # In Booking.com markdown, the larger value is usually the total
                total = max(valid_vals)
                price_per_night = round(total / nights) if nights > 0 else total
                
                # Image extraction from markdown: [![alt](img_url)](...)
                img_match = re.search(r'\!\[.*?\]\((https://cf\.bstatic\.com/[^\)]+)\)', section)
                image_url = img_match.group(1) if img_match else "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&q=80&w=720"

                deals.append({
                    "name": name, "location": city, "price_per_night": price_per_night,
                    "rating": 4.5, "reviews": 50, "pet_friendly": True,
                    "source": "booking (markdown)", "url": url, 
                    "image_url": image_url
                })
            except: continue
        return deals

    def _parse_html(self, soup, city, checkin, checkout, nights):
        deals = []
        # Find all containers that look like property cards
        cards = soup.find_all('div', {'data-testid': 'property-card'}) or \
                soup.find_all('div', class_=re.compile(r'property-card|sr_property_block'))
        
        for card in cards[:15]:
            try:
                # Skip sold out
                card_text = card.get_text().lower()
                if any(x in card_text for x in ["sold out", "ausgebucht", "no longer available", "no rooms left"]):
                    continue

                name_elem = card.find('div', {'data-testid': 'title'}) or card.find('h3')
                if not name_elem: continue
                name = name_elem.get_text(strip=True)
                
                # Highly targeted Price Parsing
                # Targeted elements: 'price-and-discounted-price' or 'price-per-night'
                price_elem = card.find(attrs={'data-testid': 'price-and-discounted-price'}) or \
                             card.find(attrs={'data-testid': 'price-per-night'}) or \
                             card.find('span', string=re.compile(r'€'))
                
                if not price_elem:
                    continue
                    
                price_text = price_elem.get_text()
                # Find all numbers in the price element specifically
                price_matches = re.findall(r'€\s*([\d\.,]+)', price_text)
                if not price_matches:
                    # Fallback to any number in that element
                    price_matches = re.findall(r'([\d\.,]+)', price_text)
                
                valid_prices = []
                for p in price_matches:
                    clean_p = p.replace('.', '').replace(',', '').strip()
                    if clean_p.isdigit():
                        val = int(clean_p)
                        if 10 < val < 50000: 
                            valid_prices.append(val)
                
                if not valid_prices: continue
                
                # On Booking.com, if we look AT THE PRICE ELEMENT:
                # - If it's a small number, it might be the nightly rate
                # - If it's a large number, it's the total
                raw_val = max(valid_prices)
                
                # Logic: If the value is very low (e.g. < 1/3 of expected total), 
                # it's likely already the nightly rate.
                # If it's higher, it's the total for the trip.
                if raw_val < (self.budget_max * 0.5) and nights > 1:
                    # Likely already nightly
                    price_per_night = raw_val
                else:
                    # Likely total
                    price_per_night = round(raw_val / nights) if nights > 0 else raw_val

                # Image
                img = card.find('img', {'data-testid': 'image'}) or card.find('img')
                image_url = ""
                if img:
                    image_url = img.get('src') or img.get('data-src') or ""
                    if image_url.startswith('//'): image_url = f"https:{image_url}"
                
                link_elem = card.find('a', href=True)
                href = link_elem['href'] if link_elem else ""
                final_url = href if href.startswith('http') else f"https://www.booking.com{href}"

                deals.append({
                    "name": name, "location": city, "price_per_night": price_per_night,
                    "rating": 4.7, "reviews": 80, "pet_friendly": True,
                    "source": "booking (html)", "url": final_url, "image_url": image_url
                })
            except Exception: continue
        return deals

    def _get_fallback_data(self, city: str, nights: int, *args, **kwargs) -> List[Dict]:
        """Emergency fallback data when all scraping fails."""
        print(f"   ⚠️ Using fallback data for {city}")
        return [
            {
                "name": f"Hotel {city} Zentrum (Fallback)",
                "location": city,
                "price_per_night": 95,
                "rating": 4.2,
                "reviews": 45,
                "pet_friendly": True,
                "source": "fallback",
                "url": "https://www.booking.com",
                "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&q=80&w=720"
            }
        ]

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
            "order=price"
        ]
        if children > 0:
            for _ in range(children):
                params.append("req_children=5")
        
        return f"{base}?{'&'.join(params)}"
