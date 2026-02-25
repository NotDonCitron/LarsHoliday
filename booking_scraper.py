import asyncio
import re
import os
import time
import httpx
from typing import Dict, List
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
from scraper_health import scraper_metrics

class BookingScraper:
    def __init__(self):
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY") or os.getenv("firecrawl_api_key")
        self.cache = cache
        self.delayer = RequestDelayer(min_delay=5, max_delay=15)
        self.budget_max = 250 # Default, updated by agent

    async def search_booking(self, city: str, checkin: str, checkout: str, adults: int = 4, children: int = 0) -> List[Dict]:
        """
        Smart search with fallback strategies.
        """
        # Specificity fix
        search_city = city
        if "," not in city:
            low_city = city.lower()
            if any(x in low_city for x in ["hamburg", "berlin", "münchen", "munich", "köln", "cologne", "heidelberg"]):
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
        ]

        for name, strategy in strategies:
            started = time.perf_counter()
            try:
                print(f"   [Booking] Trying {name} strategy for {search_city}...")
                deals = await strategy(search_city, checkin, checkout, adults, children, nights)
                duration = time.perf_counter() - started

                scraper_metrics.record(
                    source="booking",
                    strategy=name,
                    success=bool(deals),
                    duration=duration,
                    result_count=len(deals) if deals else 0,
                    error=None if deals else "no_results",
                )

                if deals and len(deals) > 0:
                    print(f"   ✅ {name} strategy succeeded: {len(deals)} deals")
                    return deals
            except Exception as e:
                duration = time.perf_counter() - started
                scraper_metrics.record(
                    source="booking",
                    strategy=name,
                    success=False,
                    duration=duration,
                    result_count=0,
                    error=str(e),
                )
                err_short = self._truncate_text(str(e), 100)
                print(f"   ❌ {name} strategy failed: {err_short}")
                continue

        fallback_started = time.perf_counter()
        fallback_deals = self._get_fallback_data(search_city, nights)
        fallback_duration = time.perf_counter() - fallback_started
        scraper_metrics.record(
            source="booking",
            strategy="fallback",
            success=bool(fallback_deals),
            duration=fallback_duration,
            result_count=len(fallback_deals),
            error=None if fallback_deals else "no_results",
        )
        return fallback_deals

    async def _search_curl(self, city: str, checkin: str, checkout: str, adults: int, children: int, nights: int) -> List[Dict]:
        """Fast strategy using local httpx request."""
        await self.delayer.wait()
        url = self._build_booking_url(city, checkin, checkout, adults, children)
        
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
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

        return []

    async def _search_firecrawl(self, city: str, checkin: str, checkout: str, adults: int, children: int, nights: int) -> List[Dict]:
        """Verified strategy using Firecrawl cloud scraping with improved extraction."""
        if not self.firecrawl_key:
            raise Exception("Firecrawl API key missing")
            
        url = self._build_booking_url(city, checkin, checkout, adults, children)
        
        async def make_firecrawl_call():
            async with httpx.AsyncClient(timeout=180.0) as client:
                return await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {self.firecrawl_key}"},
                    json={
                        "url": url, 
                        "formats": ["markdown", "html"], 
                        "waitFor": 10000,
                        "actions": [
                            {"type": "scroll", "direction": "down", "amount": 1500},
                            {"type": "wait", "milliseconds": 1500}
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
        # Split into property sections
        sections = re.split(r'###\s*\[', markdown)
        section_index = 1
        while section_index < len(sections):
            try:
                section = '[' + sections[section_index]
                name_match = re.search(r'\[([^\]]+)\]\((https://www\.booking\.com/hotel/[^\)]+)\)', section)
                if not name_match: continue
                
                name = name_match.group(1).replace('\\', '').replace('Opens in new window', '').strip()
                url = name_match.group(2).strip()
                
                # Normalize text
                section = section.replace('&nbsp;', ' ').replace('\xa0', ' ')
                
                # Find all prices
                prices = re.findall(r'€\s*([\d\.,\s]+)|([\d\.,\s]+)\s*€', section)
                potential_vals = [item for sublist in prices for item in sublist if item]
                
                valid_vals = []
                for p in potential_vals:
                    digits = "".join(re.findall(r'\d+', p))
                    if digits: valid_vals.append(int(digits))
                
                if not valid_vals: continue
                
                total = max(valid_vals)
                price_per_night = round(total / nights) if nights > 0 else total
                
                # Image extraction
                img_match = re.search(r'\!\[.*?\]\((https://cf\.bstatic\.com/[^\)]+)\)', section)
                image_url = img_match.group(1) if img_match else "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&q=80&w=720"

                deals.append({
                    "name": name, "location": city, "price_per_night": price_per_night,
                    "rating": 4.5, "reviews": 50, "pet_friendly": True,
                    "source": "booking (markdown)", "url": url, 
                    "image_url": image_url
                })
            except:
                section_index += 1
                continue
            section_index += 1
        return deals

    def _parse_html(self, soup, city, checkin, checkout, nights):
        deals = []
        # Find all containers that look like property cards
        cards = soup.find_all('div', {'data-testid': 'property-card'}) or \
                soup.find_all('div', class_=re.compile(r'property-card|sr_property_block'))
        
        if not cards:
            return []

        for card in cards[:15]:
            try:
                # Skip sold out
                card_text = card.get_text().lower()
                if any(x in card_text for x in ["sold out", "ausgebucht", "no longer available", "no rooms left", "nicht mehr verfügbar"]):
                    continue

                name_elem = card.find('div', {'data-testid': 'title'}) or card.find('h3')
                if not name_elem: continue
                name = name_elem.get_text(strip=True).replace('Opens in new window', '').strip()
                
                # Extremely Robust Price Parsing
                price_text = ""
                price_elem = card.find(attrs={'data-testid': 'price-and-discounted-price'}) or \
                             card.find(attrs={'data-testid': 'price-per-night'}) or \
                             card.find(attrs={'data-testid': 'availability-rate-information'})
                
                if price_elem:
                    price_text = price_elem.get_text()
                
                if not price_text or "€" not in price_text:
                    aria_price = card.find(attrs={'aria-label': re.compile(r'Price')})
                    if aria_price: price_text = aria_price.get('aria-label')
                
                if not price_text or "€" not in price_text:
                    price_text = card_text

                price_text = price_text.replace('&nbsp;', ' ').replace('\xa0', ' ')
                price_matches = re.findall(r'€\s*([\d\.,\s]+)|([\d\.,\s]+)\s*€|Price\s*€\s*([\d\.,\s]+)', price_text)
                potential_vals = [item for sublist in price_matches for item in sublist if item]
                
                valid_prices = []
                for p in potential_vals:
                    clean_p = "".join(re.findall(r'\d+', p))
                    if clean_p:
                        val = int(clean_p)
                        if 10 < val < 50000: valid_prices.append(val)
                
                if not valid_prices:
                    all_nums = re.findall(r'\d+[\d\.,]*', price_text)
                    for n in all_nums:
                        clean_n = "".join(re.findall(r'\d+', n))
                        if clean_n and 20 < int(clean_n) < 10000:
                            valid_prices.append(int(clean_n))

                if not valid_prices: continue
                
                raw_val = max(valid_prices)
                if raw_val < (self.budget_max * 0.7) and nights > 2:
                    price_per_night = raw_val
                else:
                    price_per_night = round(raw_val / nights) if nights > 0 else raw_val

                # Images (capture up to 5)
                images = []
                # Strategy 1: Look for all images in the card
                img_elements = card.find_all('img')
                for img in img_elements:
                    src = img.get('src') or img.get('data-src') or \
                          (img.get('srcset', '').split(',')[0].split(' ')[0] if img.get('srcset') else "")
                    if src and "bstatic.com" in src:
                        if src.startswith('//'): src = f"https:{src}"
                        # Increase quality and variety
                        src = re.sub(r'square\d+', 'max500', src)
                        if src not in images:
                            images.append(src)
                
                # Strategy 2: If we still have only 1 image, look for hidden thumbnails in data-attributes
                if len(images) < 2:
                    # Sometimes Booking hides extra URLs in string attributes
                    card_str = str(card)
                    extra_imgs = re.findall(r'https://cf\.bstatic\.com/xdata/images/hotel/max500/[^"\']+', card_str)
                    for img in extra_imgs:
                        if img not in images:
                            images.append(img)
                        if len(images) >= 5: break

                image_url = images[0] if images else "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&q=80&w=720"

                link_elem = card.find('a', href=True)
                href = link_elem['href'] if link_elem else ""
                final_url = href if href.startswith('http') else f"https://www.booking.com{href}"

                deals.append({
                    "name": name, "location": city, "price_per_night": price_per_night,
                    "rating": 4.7, "reviews": 80, "pet_friendly": True,
                    "source": "booking (html)", "url": final_url, 
                    "image_url": image_url,
                    "images": images
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

    def _truncate_text(self, value: object, limit: int = 120) -> str:
        text = str(value)
        if len(text) <= limit:
            return text

        result = ""
        idx = 0
        while idx < limit and idx < len(text):
            result = result + text[idx]
            idx += 1
        return result

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
