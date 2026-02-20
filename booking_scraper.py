"""
Booking.com Scraper using Patchright for maximum reliability
Searches for pet-friendly accommodations with full JS rendering
"""

import asyncio
import re
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote, urlparse

try:
    from patchright.async_api import async_playwright
    PATCHRIGHT_AVAILABLE = True
except ImportError:
    PATCHRIGHT_AVAILABLE = False


class BookingScraper:
    """
    Scrapes Booking.com for pet-friendly accommodations using Patchright
    """

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    async def launch(self):
        """Launch undetected browser"""
        if not PATCHRIGHT_AVAILABLE:
            raise ImportError("patchright not installed")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        )

    async def close(self):
        """Close browser sessions"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def search_booking(
        self,
        city: str,
        checkin: str,
        checkout: str,
        adults: int = 4
    ) -> List[Dict]:
        """
        Search Booking.com using browser automation
        """
        print(f"   [Patchright] Searching Booking.com for {city}...")

        if not self.browser:
            await self.launch()

        page = await self.context.new_page()
        url = self._build_booking_url(city, checkin, checkout, adults)

        try:
            # Navigate with a generous timeout
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Wait for results to load
            await asyncio.sleep(5)
            
            # Handle potential cookie banners or popups
            try:
                # Common "Accept Cookies" button selector
                await page.click('button#onetrust-accept-btn-handler', timeout=3000)
            except:
                pass

            # Scroll to trigger lazy loading of images
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(2)

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Calculate nights
            d1 = datetime.strptime(checkin, "%Y-%m-%d")
            d2 = datetime.strptime(checkout, "%Y-%m-%d")
            nights = max(1, (d2 - d1).days)

            deals = self._parse_html(soup, city, checkin, checkout, adults, nights)

            if deals:
                print(f"   [Patchright] Found {len(deals)} properties on Booking.com")
                return deals
            else:
                print(f"   [Patchright] No properties found on Booking.com")
                return []

        except Exception as e:
            print(f"   [Patchright] Warning: Could not scrape Booking.com: {str(e)[:100]}")
            return []
        finally:
            await page.close()

    def _build_booking_url(
        self,
        city: str,
        checkin: str,
        checkout: str,
        adults: int
    ) -> str:
        """Build Booking.com search URL with pet-friendly filter"""
        base_url = "https://www.booking.com/searchresults.html"
        params = [
            f"ss={quote(city)}",
            f"checkin={checkin}",
            f"checkout={checkout}",
            f"group_adults={adults}",
            "group_children=0",
            "no_rooms=1",
            "nflt=ht_id%3D220;hotelfacility%3D14", # Apartments + Pet-friendly
        ]
        return f"{base_url}?{'&'.join(params)}"

    def _parse_html(self, soup: BeautifulSoup, city: str, checkin: str, checkout: str, adults: int, nights: int) -> List[Dict]:
        """Parse Booking.com HTML to extract property data with robust heuristics"""
        deals = []
        property_cards = soup.find_all('div', {'data-testid': 'property-card'})
        
        if not property_cards:
            # Fallback to older class names
            property_cards = soup.find_all('div', class_=re.compile(r'sr_property_block|property_card'))

        for card in property_cards[:15]:
            try:
                # 1. Name
                name_elem = card.find('div', {'data-testid': 'title'}) or card.find('h3')
                name = name_elem.get_text(strip=True) if name_elem else "Unbekannte Unterkunft"

                # 2. Price Parsing (Robust)
                price_elem = card.find('span', {'data-testid': 'price-and-discounted-price'}) or \
                             card.find('div', class_=re.compile(r'prco-valign-middle-helper')) or \
                             card.find(string=re.compile(r'€|€\s*\d+'))
                
                price_text = ""
                if price_elem:
                    price_text = price_elem.get_text(strip=True) if hasattr(price_elem, 'get_text') else str(price_elem)
                
                # Extract all numbers from price string
                numbers = re.findall(r'[\d\.,]+', price_text.replace('\xa0', '').replace(' ', ''))
                total_price = 0
                if numbers:
                    # Take the last number (usually the current price after discounts)
                    price_val = numbers[-1].replace('.', '').replace(',', '')
                    total_price = int(price_val) if price_val.isdigit() else 0
                
                # Fallback: Check if price is hidden in parent container
                if total_price == 0:
                    card_text = card.get_text()
                    price_matches = re.findall(r'€\s*([\d\.,]+)', card_text)
                    if price_matches:
                        price_val = price_matches[-1].replace('.', '').replace(',', '')
                        total_price = int(price_val)
                
                price_per_night = round(total_price / nights) if total_price > 0 else 0

                # 3. Rating
                rating_elem = card.find('div', {'data-testid': 'review-score'}) or card.find('div', class_=re.compile(r'review-score'))
                rating = 4.0
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating_match = re.search(r'(\d+[\.,]\d+)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group().replace(',', '.')) / 2
                rating = min(5.0, rating)

                # 4. Reviews
                review_elem = card.find('div', {'data-testid': 'review-count'}) or card.find('div', class_=re.compile(r'review-count'))
                reviews = 50
                if review_elem:
                    review_text = review_elem.get_text(strip=True)
                    review_match = re.search(r'\d+', review_text.replace('.', '').replace(',', ''))
                    reviews = int(review_match.group()) if review_match else 50

                # 5. URL
                link_elem = card.find('a', {'data-testid': 'title-link'}) or card.find('a', href=True)
                raw_url = link_elem['href'] if link_elem and link_elem.get('href') else ""
                if raw_url.startswith('/'):
                    raw_url = f"https://www.booking.com{raw_url}"
                clean_url = raw_url.split('?')[0] if '?' in raw_url else raw_url
                final_url = f"{clean_url}?checkin={checkin}&checkout={checkout}&group_adults={adults}"

                # 6. Image (Robust)
                img_elem = card.find('img', {'data-testid': 'image'}) or card.find('img')
                image_url = ""
                if img_elem:
                    # Check srcset first for higher quality
                    srcset = img_elem.get('srcset', '')
                    if srcset:
                        # Take the first URL from srcset
                        image_url = srcset.split(',')[0].split(' ')[0]
                    else:
                        image_url = img_elem.get('src') or img_elem.get('data-src') or ""
                
                # Ensure it's an absolute URL
                if image_url and image_url.startswith('//'):
                    image_url = f"https:{image_url}"

                deals.append({
                    "name": name,
                    "location": city,
                    "price_per_night": price_per_night,
                    "rating": rating,
                    "reviews": reviews,
                    "pet_friendly": True,
                    "source": "booking.com",
                    "url": final_url,
                    "image_url": image_url
                })
            except Exception as e:
                print(f"      [Debug] Error parsing card: {e}")
                continue

        return deals
