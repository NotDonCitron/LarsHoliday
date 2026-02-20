"""
Enhanced Airbnb Scraper with Adaptive Strategy Selection

Strategy (ordered by AdaptiveRouter based on recent success rates):
1. curl-cffi with session warming (fast, ~3-5s)
2. Patchright with XHR interception (reliable, ~15-25s)
3. Static fallback (always works)

Key improvements over original:
- Session warming (cookies before search)
- Expanded browser impersonation (Chrome/Edge/Safari)
- Adaptive strategy ordering via scraper_health metrics
- Multi-path JSON extraction (niobeClientData + StaysSearch API)
- Patchright reuses browser instance across searches
- Patchright uses networkidle instead of hard-coded sleep
- Cache integration at search entry point
"""

from curl_cffi import requests  # pyre-ignore[21]
from typing import List, Dict, Optional, Any, Union, Callable, Awaitable
from bs4 import BeautifulSoup  # pyre-ignore[21]
import re
import asyncio
import random
import time
import json as json_module
from datetime import datetime
from dotenv import load_dotenv  # pyre-ignore[21]

load_dotenv()

from urllib.parse import quote

# Import rate limit bypass utilities
from rate_limit_bypass import (  # pyre-ignore[21]
    RequestDelayer,
    ExponentialBackoff,
    cache,
    session_warmer,
    get_random_user_agent,
)

# Import health tracking
from scraper_health import scraper_metrics, adaptive_router  # pyre-ignore[21]


class EnhancedAirbnbScraper:
    """
    Enhanced Airbnb scraper with curl-cffi, session warming,
    and expanded browser impersonation.
    """
    
    def __init__(self):
        self.delayer = RequestDelayer(min_delay=3, max_delay=8)
        self.backoff = ExponentialBackoff(max_retries=3, base_delay=10)
    
    def _get_random_impersonation(self):
        """Return a diverse browser impersonation."""
        browsers = [
            "chrome120", "chrome119", "chrome110",
            "edge101", "edge99",
            "safari15_3", "safari15_5",
        ]
        return random.choice(browsers)
    
    def _build_url(self, region: str, checkin: str, checkout: str, adults: int) -> str:
        safe_region = quote(region)
        return f"https://www.airbnb.com/s/{safe_region}/homes?checkin={checkin}&checkout={checkout}&adults={adults}"
    
    def _build_headers(self) -> dict:
        """Build realistic request headers."""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice([
                'en-US,en;q=0.9',
                'en-GB,en;q=0.9',
                'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
                'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
    
    async def search_airbnb(
        self,
        region: str,
        checkin: str,
        checkout: str,
        adults: int = 4
    ) -> List[Dict]:
        """Search Airbnb with curl-cffi and session warming."""
        print(f"   [Enhanced] Searching Airbnb for {region}...")
        
        start_time = time.time()
        session = requests.Session()
        impersonation = self._get_random_impersonation()
        
        # Warm session (collect cookies from homepage first)
        await session_warmer.warm_session(session, 'www.airbnb.com', impersonation)
        
        await self.delayer.wait()
        
        url = self._build_url(region, checkin, checkout, adults)
        
        while True:
            try:
                response = session.get(
                    url,
                    impersonate=impersonation,
                    headers=self._build_headers(),
                    timeout=30,
                    allow_redirects=True
                )
                
                if response.status_code == 429:
                    self.delayer.notify_pressure()
                    await self.backoff.wait()
                    if not self.backoff.should_retry():
                        duration = time.time() - start_time
                        scraper_metrics.record('airbnb', 'curl-cffi', False, duration, error='429 rate limited')
                        return []  # Return empty — let SmartScraper handle fallback
                    continue
                
                if response.status_code != 200:
                    duration = time.time() - start_time
                    scraper_metrics.record('airbnb', 'curl-cffi', False, duration, error=f'HTTP {response.status_code}')
                    return []
                
                self.backoff.reset()
                break
                
            except Exception as e:
                await self.backoff.wait()
                if not self.backoff.should_retry():
                    duration = time.time() - start_time
                    scraper_metrics.record('airbnb', 'curl-cffi', False, duration, error=str(e)[:100])  # pyre-ignore[16]
                    return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        deals = self._parse_html(soup, region, checkin, checkout, adults)
        
        session.close()
        
        duration = time.time() - start_time
        scraper_metrics.record('airbnb', 'curl-cffi', len(deals) > 0, duration, result_count=len(deals))
        
        if deals:
            print(f"   [Enhanced] Found {len(deals)} properties ({duration:.1f}s)")
        else:
            print(f"   [Enhanced] No results from curl-cffi ({duration:.1f}s)")
        
        return deals
    
    def _parse_html(self, soup: BeautifulSoup, region: str, checkin: str, checkout: str, required_capacity: int) -> List[Dict]:
        """Parse Airbnb HTML with multiple extraction paths."""
        deals = []
        script_tags = soup.find_all('script', type='application/json')
        
        for script in script_tags:
            try:
                data = script.string
                if not data:
                    continue
                
                parsed = json_module.loads(data)
                listings = self._find_listings_in_json(parsed)
                
                if listings:
                    for item in listings[:20]:  # pyre-ignore[16]
                        deal = self._extract_listing(item, region, checkin, checkout, required_capacity)
                        if deal:
                            deals.append(deal)
                    if deals:
                        return deals
            except (json_module.JSONDecodeError, TypeError, KeyError):
                continue
        
        return deals
    
    def _find_listings_in_json(self, data) -> list:
        """
        Search for listings in Airbnb JSON responses.
        Handles multiple JSON structures that Airbnb uses.
        """
        # Path 1: niobeClientData (most common)
        if isinstance(data, dict) and 'niobeClientData' in data:
            niobe = data['niobeClientData']
            if isinstance(niobe, list):
                # Try direct format: [key, {data}]
                if len(niobe) > 1 and isinstance(niobe[1], dict):
                    results = self._dig_for_search_results(niobe[1])
                    if results:
                        return results
                # Try nested format: [[key, {data}], ...]
                for item in niobe:
                    if isinstance(item, list) and len(item) > 1 and isinstance(item[1], dict):
                        results = self._dig_for_search_results(item[1])  # pyre-ignore[16]
                        if results:
                            return results
                    elif isinstance(item, dict):
                        results = self._dig_for_search_results(item)  # pyre-ignore[16]
                        if results:
                            return results
        
        # Path 2: Direct data.presentation path
        if isinstance(data, dict):
            results = self._dig_for_search_results(data)
            if results:
                return results
        
        # Path 3: Iterate top-level keys looking for search results
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    results = self._dig_for_search_results(value)
                    if results:
                        return results
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            results = self._dig_for_search_results(item)
                            if results:
                                return results
        
        return []
    
    def _dig_for_search_results(self, obj: dict) -> list:
        """Recursively search for searchResults in a nested dict."""
        if not isinstance(obj, dict):
            return []
        
        # Direct path
        try:
            pres = obj.get('data', {}).get('presentation', {})
            search = pres.get('staysSearch', {})
            results = search.get('results', {})
            listings = results.get('searchResults', [])
            if listings:
                return listings
        except (AttributeError, TypeError):
            pass
        
        # Try alternate paths
        for key in ['presentation', 'staysSearch', 'results', 'searchResults']:
            if key in obj:
                val = obj[key]
                if isinstance(val, list) and len(val) > 0:
                    return val
                if isinstance(val, dict):
                    result = self._dig_for_search_results(val)
                    if result:
                        return result
        
        return []
    
    def _extract_listing(self, item: dict, region: str, checkin: str, checkout: str, required_capacity: int) -> Optional[Dict]:
        try:
            def get_val(key):
                val = item.get(key)
                if val is None and item.get('listing'):
                    val = item['listing'].get(key)
                return val
            
            capacity = get_val('personCapacity')
            if capacity and int(capacity) < required_capacity:
                return None
            
            name = get_val('title') or 'Airbnb Property'
            
            price_obj = item.get('structuredDisplayPrice') or {}
            price_line = price_obj.get('primaryLine') or {}
            price_text = price_line.get('discountedPrice') or price_line.get('price') or '€60'
            
            raw_price = 60
            match = re.search(r'\d+', price_text.replace(',', '').replace('\u00a0', ''))
            if match:
                raw_price = int(match.group())
            
            # Filter out invalid "€1" prices
            if raw_price < 20:
                return None
            
            price = raw_price
            if price_line.get('qualifier') == 'total':
                try:
                    nights = (datetime.strptime(checkout, "%Y-%m-%d") - datetime.strptime(checkin, "%Y-%m-%d")).days
                    if nights > 0:
                        price = raw_price // nights
                except Exception:
                    pass
            
            rating_text = get_val('avgRatingLocalized') or '4.5'
            rating = 4.5
            match = re.search(r'(\d+\.?\d*)', rating_text)
            if match:
                rating = float(match.group(1))
            
            reviews_text = get_val('avgRatingA11yLabel') or '50 reviews'
            reviews = 50
            match = re.search(r'(\d+)', reviews_text)
            if match:
                reviews = int(match.group(1))
            
            prop_id = None
            for key in ['id', 'propertyId', 'listingId']:
                if item.get(key):
                    prop_id = item[key]
                    break
            if not prop_id and item.get('listing'):
                prop_id = item['listing'].get('id')
            
            if not prop_id:
                return None
            
            # Prefer the actual listing URL from Airbnb's data over constructed URL
            url = None
            listing_data = item.get('listing', {})
            # Try contextualPicturesPageUrl (contains full room path)
            for pic in listing_data.get('contextualPictures', []):
                page_url = pic.get('contextualPicturesPageUrl')
                if page_url and '/rooms/' in str(page_url):
                    url = f"https://www.airbnb.com{page_url}" if str(page_url).startswith('/') else str(page_url)
                    break
            # Try listing URL directly
            if not url:
                for key in ['listingUrl', 'pdpUrlType', 'canonicalUrl']:
                    val = listing_data.get(key)
                    if val and '/rooms/' in str(val):
                        url = f"https://www.airbnb.com{val}" if str(val).startswith('/') else str(val)
                        break
            # Fall back to constructed URL is DANGEROUS because internal IDs don't match room IDs
            # If we don't have a valid URL, return None so we fall back to HTML parsing
            if not url:
                return None
            
            # Ensure URL has query params
            if '?' not in url:
                url += f"?check_in={checkin}&check_out={checkout}&guests={required_capacity}"
            
            return {
                "name": name,
                "location": region,
                "price_per_night": price,
                "rating": rating,
                "reviews": reviews,
                "pet_friendly": True,
                "source": "airbnb",
                "url": url
            }
        except Exception:
            return None
    
    def _get_fallback_data(self, region: str, checkin: str, checkout: str, adults: int) -> List[Dict]:
        def get_url():
            return f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}"
        
        fallback_properties = {
            "Amsterdam": [
                {"name": "City Center Apartment", "location": "Amsterdam", "price_per_night": 145, "rating": 4.5, "reviews": 120, "pet_friendly": True, "source": "airbnb (fallback)", "url": get_url()},
                {"name": "Canal Houseboat", "location": "Amsterdam", "price_per_night": 180, "rating": 4.8, "reviews": 89, "pet_friendly": True, "source": "airbnb (fallback)", "url": get_url()},
            ],
            "Berlin": [
                {"name": "Trendy Mitte Apartment", "location": "Berlin Mitte", "price_per_night": 95, "rating": 4.6, "reviews": 156, "pet_friendly": True, "source": "airbnb (fallback)", "url": get_url()},
            ],
        }
        return fallback_properties.get(region, [
            {"name": f"Charming {region} Stay", "location": region, "price_per_night": 85, "rating": 4.5, "reviews": 25, "pet_friendly": True, "source": "airbnb (fallback)", "url": get_url()},
        ])


class PatchrightAirbnbScraperImproved:
    """
    Improved Patchright scraper with:
    - Persistent browser instance (reused across searches)
    - networkidle wait instead of hard-coded sleep
    - XHR response interception for direct JSON extraction
    - Randomized fingerprints
    """
    
    def __init__(self) -> None:
        self.browser: Any = None
        self.playwright: Any = None
        self._search_count: int = 0
        self._max_searches_before_restart: int = 10
    
    async def launch(self):
        """Launch Patchright browser."""
        try:
            from patchright.async_api import async_playwright  # pyre-ignore[21]
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self._search_count = 0
        except ImportError:
            raise Exception("Patchright not installed. Run: pip install patchright")
    
    async def close(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
    
    async def _ensure_browser(self):
        """Ensure browser is running, restart if needed."""
        if self.browser is None or self._search_count >= self._max_searches_before_restart:
            if self.browser:
                await self.close()
            await self.launch()
    
    async def search_airbnb(
        self,
        region: str,
        checkin: str,
        checkout: str,
        adults: int = 4
    ) -> List[Dict]:
        """Search Airbnb with Patchright — persistent browser, smart waits."""
        await self._ensure_browser()
        
        print(f"   [Patchright] Searching Airbnb for {region}...")
        start_time = time.time()
        
        # Randomize fingerprint
        from rate_limit_bypass import get_random_fingerprint  # pyre-ignore[21]
        fingerprint = get_random_fingerprint()
        
        context = await self.browser.new_context(
            viewport=fingerprint['viewport'],
            user_agent=fingerprint['user_agent'],
            locale=fingerprint['locale'],
        )
        
        page = await context.new_page()
        
        # Set up XHR interception to capture JSON data
        captured_json = []
        
        async def handle_response(response):
            """Intercept API responses for direct JSON extraction."""
            try:
                url = response.url
                if ('StaysSearch' in url or 'search' in url) and response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        body = await response.json()
                        captured_json.append(body)
            except Exception:
                pass
        
        page.on('response', handle_response)
        
        url = f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}"
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Smart wait: use networkidle with timeout instead of hard 10s sleep
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                pass  # Timeout is fine, we have enough data
            
            # Wait for listing cards to appear
            try:
                await page.wait_for_selector('[data-testid="card-container"]', timeout=8000)
            except Exception:
                # Try waiting a bit more for dynamic content
                await asyncio.sleep(3)
            
            self._search_count += 1
            
            # Strategy 1: Try captured XHR JSON data first
            deals = []
            for json_data in captured_json:
                listings = self._find_listings_in_xhr(json_data)
                if listings:
                    for item in listings[:20]:  # pyre-ignore[16]
                        deal = self._extract_listing_from_xhr(item, region, checkin, checkout, adults)
                        if deal:
                            deals.append(deal)
                    if deals:
                        break
            
            # Strategy 2: Fall back to HTML parsing
            if not deals:
                content = await page.content()
                deals = self._parse_content(content, region, checkin, checkout, adults)
            
            duration = time.time() - start_time
            
            if deals:
                print(f"   [Patchright] Found {len(deals)} properties ({duration:.1f}s)")
                scraper_metrics.record('airbnb', 'patchright', True, duration, result_count=len(deals))
            else:
                print(f"   [Patchright] No listings found ({duration:.1f}s)")
                scraper_metrics.record('airbnb', 'patchright', False, duration, error='No listings parsed')
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"   [Patchright] Error: {e}")
            scraper_metrics.record('airbnb', 'patchright', False, duration, error=str(e)[:100])  # pyre-ignore[16]
            deals = []
        finally:
            await page.close()
            await context.close()
        
        return deals
    
    def _find_listings_in_xhr(self, data) -> list:
        """Extract listings from intercepted XHR JSON response."""
        if not isinstance(data, dict):
            return []
        
        # Try common response structures
        for path in [
            lambda d: d.get('data', {}).get('presentation', {}).get('staysSearch', {}).get('results', {}).get('searchResults', []),
            lambda d: d.get('data', {}).get('searchResults', []),
            lambda d: d.get('searchResults', []),
        ]:
            try:
                results = path(data)
                if results and isinstance(results, list):
                    return results
            except (AttributeError, TypeError):
                continue
        
        return []
    
    def _extract_listing_from_xhr(self, item: dict, region: str, checkin: str, checkout: str, adults: int = 4) -> Optional[Dict]:
        """Extract a deal from XHR JSON listing data."""
        try:
            listing = item.get('listing', item)
            name = listing.get('title') or listing.get('name') or 'Airbnb Property'
            
            # Extract price
            price_obj = item.get('structuredDisplayPrice') or item.get('pricingQuote') or {}
            price_line = price_obj.get('primaryLine') or {}
            price_text = price_line.get('discountedPrice') or price_line.get('price') or '€80'
            
            raw_price = 80
            match = re.search(r'\d+', price_text.replace(',', '').replace('\u00a0', ''))
            if match:
                raw_price = int(match.group())
            
            if raw_price < 20:
                return None
            
            # Get rating
            rating = 4.5
            for key in ['avgRatingLocalized', 'avgRating', 'starRating']:
                val = listing.get(key)
                if val:
                    match = re.search(r'(\d+\.?\d*)', str(val))
                    if match:
                        rating = float(match.group(1))
                        break
            
            # Get reviews
            reviews = 10
            for key in ['avgRatingA11yLabel', 'reviewsCount', 'visibleReviewCount']:
                val = listing.get(key)
                if val:
                    match = re.search(r'(\d+)', str(val))
                    if match:
                        reviews = int(match.group(1))
                        break
            
            # Get ID
            prop_id = listing.get('id') or item.get('id')
            if not prop_id:
                return None
            
            # Prefer actual listing URL from Airbnb data
            url = None
            for pic in listing.get('contextualPictures', []):
                page_url = pic.get('contextualPicturesPageUrl')
                if page_url and '/rooms/' in str(page_url):
                    url = f"https://www.airbnb.com{page_url}" if str(page_url).startswith('/') else str(page_url)
                    break
            if not url:
                for key in ['listingUrl', 'pdpUrlType', 'canonicalUrl']:
                    val = listing.get(key)
                    if val and '/rooms/' in str(val):
                        url = f"https://www.airbnb.com{val}" if str(val).startswith('/') else str(val)
                        break
            if not url:
                return None
            
            if '?' not in url:
                url += f"?check_in={checkin}&check_out={checkout}&adults={adults}"
            
            return {
                "name": name,
                "location": region,
                "price_per_night": raw_price,
                "rating": min(5.0, rating),
                "reviews": reviews,
                "pet_friendly": True,
                "source": "airbnb (patchright)",
                "url": url
            }
        except Exception:
            return None
    
    def _parse_content(self, html: str, region: str, checkin: str, checkout: str, adults: int = 4) -> List[Dict]:
        """Parse rendered HTML content for listing cards."""
        deals = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try to extract from JSON in script tags first (more reliable)
        script_tags = soup.find_all('script', type='application/json')
        for script in script_tags:
            try:
                data = script.string
                if not data:
                    continue
                parsed = json_module.loads(data)
                # Reuse the EnhancedAirbnbScraper's multi-path extraction
                scraper = EnhancedAirbnbScraper()
                listings = scraper._find_listings_in_json(parsed)
                if listings:
                    for item in listings[:20]:  # pyre-ignore[16]
                        deal = scraper._extract_listing(item, region, checkin, checkout, adults)
                        if deal:
                            deal['source'] = 'airbnb (patchright)'
                            deals.append(deal)
                    if deals:
                        return deals
            except Exception:
                continue
        
        # Fall back to card parsing
        cards = soup.find_all('div', {'data-testid': 'card-container'})
        
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = max(1, (d2 - d1).days)
        
        for card in cards[:20]:
            try:
                title_elem = card.find('div', {'data-testid': 'listing-card-title'})
                name = title_elem.get_text(strip=True) if title_elem else None
                
                link = card.find('a', href=True)
                url = ""
                if link:
                    if not name and link.get('aria-label'):
                         name = link['aria-label'].split(',')[0] # Often "Listing name, rating..."
                    
                    if link.get('href'):
                        href = link['href']
                        url = f"https://www.airbnb.com{href}" if href.startswith('/') else href

                if not name or len(name) < 3:
                     name = "Airbnb Stay"
                
                card_text = card.get_text()
                
                # Robust price extraction
                price_per_night = 100
                # Match prices like €123, € 1,234, €1.234
                price_matches = re.findall(r'€\s*([\d,.]+)', card_text)
                valid_prices = []
                for p in price_matches:
                    try:
                        # cleanup: remove thousand vars (. or , depending on locale, usually , in scraping)
                        clean_p = p.replace(',', '').replace('.', '')
                        # Note: if price has cents, this might be wrong, but Airbnb usually whole numbers for browsing
                        val = int(clean_p)
                        if val > 10: # Filter out "€1" placeholders
                            valid_prices.append(val)
                    except:
                        continue
                
                if valid_prices:
                    price_per_night = min(valid_prices) # Usually simplest is nightly, total is higher
                
                # Robust rating extraction - require decimal or "Review" context
                rating = 4.5
                # Look for "4.85 (120)" pattern
                rating_match = re.search(r'(\d\.\d{1,2})\s*\(', card_text) 
                if not rating_match:
                     rating_match = re.search(r'(\d\.\d{1,2})', card_text)
                
                if rating_match:
                    try:
                        r_val = float(rating_match.group(1))
                        if 1.0 <= r_val <= 5.0:
                            rating = r_val
                    except:
                        pass
                
                reviews = 10
                reviews_match = re.search(r'(\d+)\s*review', card_text, re.IGNORECASE)
                if reviews_match:
                    reviews = int(reviews_match.group(1))

                location_elem = card.find('div', {'data-testid': 'listing-card-subtitle'})
                location = location_elem.get_text(strip=True) if location_elem else region
                
                deals.append({
                    "name": name,
                    "location": location if location else region,
                    "price_per_night": price_per_night,
                    "rating": min(5.0, rating),
                    "reviews": reviews,
                    "pet_friendly": True,
                    "source": "airbnb (patchright)",
                    "url": url
                })
            except Exception:
                continue
        
        return deals
    
    def _get_fallback_data(self, region: str, checkin: str, checkout: str, adults: int) -> List[Dict]:
        return []  # Empty fallback — prefer curl results


class SmartAirbnbScraper:
    """
    Smart scraper with adaptive strategy selection:
    1. Check cache first
    2. Use AdaptiveRouter to order strategies by recent success rate
    3. Record metrics for self-healing behavior
    """
    
    def __init__(self) -> None:
        self.enhanced_scraper: EnhancedAirbnbScraper = EnhancedAirbnbScraper()
        self.patchright_scraper: Optional[PatchrightAirbnbScraperImproved] = None
    
    async def search_airbnb(
        self,
        region: str,
        checkin: str,
        checkout: str,
        adults: int = 4,
        track_prices: bool = True
    ) -> List[Dict]:
        """Smart search with cache check, adaptive routing, and metrics."""
        
        # 1. Check cache first
        cache_key = cache.make_key('airbnb', region=region, checkin=checkin, checkout=checkout, adults=str(adults))
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        # 2. Get strategy order from AdaptiveRouter
        strategy_map: Dict[str, Callable[[str, str, str, int], Awaitable[List[Dict]]]] = {
            'curl-cffi': self._search_curl,
            'patchright': self._search_patchright,
            'fallback': self._get_fallback,
        }
        
        strategy_order = adaptive_router.get_strategy_order(
            'airbnb',
            available_strategies=list(strategy_map.keys())
        )
        
        print(f"   [Smart] Strategy order: {' → '.join(strategy_order)}")
        
        # 3. Try strategies in adaptive order
        for name in strategy_order:
            strategy = strategy_map[name]
            try:
                deals = await strategy(region, checkin, checkout, adults)
                
                if deals and len(deals) > 0:
                    print(f"   [Smart] ✓ {name} succeeded: {len(deals)} deals")
                    
                    # Cache successful results
                    cache.set(cache_key, deals)
                    
                    if track_prices:
                        self._track_prices(deals)
                    
                    return deals
                else:
                    print(f"   [Smart] ✗ {name}: no results")
                    
            except Exception as e:
                print(f"   [Smart] ✗ {name} failed: {str(e)[:50]}")  # pyre-ignore[16]
                continue
        
        # All strategies exhausted, use fallback
        fallback_deals = await self._get_fallback(region, checkin, checkout, adults)
        return fallback_deals
    
    def _track_prices(self, deals: List[Dict]):
        """Track prices for the top deals."""
        try:
            from rate_limit_bypass import price_alerts  # pyre-ignore[21]
            for deal in deals[:5]:  # pyre-ignore[16]
                if deal.get('url'):
                    prop_id = (
                        deal.get('url', '').split('/rooms/')[1].split('?')[0]
                        if '/rooms/' in deal.get('url', '')
                        else deal.get('name', '')[:20]  # pyre-ignore[16]
                    )
                    price_alerts.track_property(
                        property_id=prop_id,
                        name=deal.get('name', 'Unknown'),
                        price=deal.get('price_per_night', 0),
                        url=deal.get('url', ''),
                        source=deal.get('source', 'unknown')
                    )
        except Exception:
            pass  # Price tracking is non-critical
    
    async def _search_curl(self, region: str, checkin: str, checkout: str, adults: int) -> List[Dict]:
        return await self.enhanced_scraper.search_airbnb(region, checkin, checkout, adults)
    
    async def _search_patchright(self, region: str, checkin: str, checkout: str, adults: int) -> List[Dict]:
        try:
            if not self.patchright_scraper:
                self.patchright_scraper = PatchrightAirbnbScraperImproved()
            
            # At this point patchright_scraper is guaranteed to be non-None
            scraper = self.patchright_scraper
            deals = await scraper.search_airbnb(region, checkin, checkout, adults)
            return deals
        except ImportError:
            raise Exception("Patchright not available")
    
    async def _get_fallback(self, region: str, checkin: str, checkout: str, adults: int) -> List[Dict]:
        scraper_metrics.record('airbnb', 'fallback', True, 0.0, result_count=1)
        return self.enhanced_scraper._get_fallback_data(region, checkin, checkout, adults)


async def test_smart_scraper():
    print("=" * 60)
    print("TESTING SMART AIRBNB SCRAPER")
    print("=" * 60)
    
    scraper = SmartAirbnbScraper()
    
    deals = await scraper.search_airbnb(
        region="Amsterdam",
        checkin="2026-02-15",
        checkout="2026-02-22",
        adults=4
    )
    
    print(f"\nFound {len(deals)} deals:")
    for i, deal in enumerate(deals[:5], 1):  # pyre-ignore[16]
        print(f"\n#{i} - {deal['name']}")
        print(f"   Location: {deal['location']}")
        print(f"   Price: €{deal['price_per_night']}/night")
        print(f"   Rating: {deal['rating']}/5.0 ({deal['reviews']} reviews)")
        print(f"   Source: {deal['source']}")
    
    # Print health report
    from scraper_health import health_reporter  # pyre-ignore[21]
    print(health_reporter.generate())
    
    from rate_limit_bypass import price_alerts  # pyre-ignore[21]
    print(price_alerts.list_tracked())


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_smart_scraper())
