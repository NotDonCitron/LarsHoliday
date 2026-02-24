import asyncio
import re
import os
import httpx
import random
from typing import List, Dict
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

class PatchrightAirbnbScraper:
    def __init__(self):
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY") or os.getenv("firecrawl_api_key")
        self.cache = cache
        self.delayer = RequestDelayer(min_delay=5, max_delay=15)

    async def search_airbnb(self, region: str, checkin: str, checkout: str, adults: int = 4, children: int = 0, pets: int = 1, budget_max: int = 500) -> List[Dict]:
        """
        Smart search with fallback strategies.
        """
        # Specificity fix: If region is a single word and likely European, append "Germany" or "Netherlands"
        # to avoid landing in "Hamburg, NY" etc.
        search_region = region
        if "," not in region:
            low_region = region.lower()
            if any(x in low_region for x in ["hamburg", "berlin", "münchen", "munich", "köln", "cologne"]):
                search_region = f"{region}, Germany"
            elif any(x in low_region for x in ["amsterdam", "rotterdam", "utrecht", "zandvoort", "texel", "zeeland"]):
                search_region = f"{region}, Netherlands"

        # Calculate nights for parsing
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
                print(f"   [Scraper] Trying {name} strategy for {search_region}...")
                deals = await strategy(search_region, checkin, checkout, adults, children, pets, budget_max, nights)
                if deals and len(deals) > 0:
                    print(f"   ✅ {name} strategy succeeded: {len(deals)} deals")
                    return deals
            except Exception as e:
                print(f"   ❌ {name} strategy failed: {str(e)[:100]}")
                continue
        
        return self._get_fallback_data(search_region, nights)

    async def _search_curl(self, region: str, checkin: str, checkout: str, adults: int, children: int, pets: int, budget_max: int, nights: int) -> List[Dict]:
        """
        Fast strategy using local httpx request with rotated User-Agents.
        Note: Airbnb often blocks this, hence why it's the first (fast) attempt.
        """
        await self.delayer.wait()
        url = f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}&children={children}&pets={pets}&price_max={budget_max}"
        
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                # Basic check for block
                if "dropped her ice cream" in response.text or "unusual activity" in response.text:
                    raise Exception("429 Blocked by Airbnb (Ice Cream/Bot detection)")
                
                # If we got real HTML, parse it (parsing logic might need to be different for raw HTML vs Markdown)
                # For now, we reuse the markdown parser if the text looks okay, or return empty to trigger next strategy
                return [] # Placeholder: HTML parsing is complex, fallback to Firecrawl for now
            elif response.status_code == 429:
                raise Exception("429 Too Many Requests")
            else:
                raise Exception(f"HTTP Error {response.status_code}")

    async def _search_firecrawl(self, region: str, checkin: str, checkout: str, adults: int, children: int, pets: int, budget_max: int, nights: int) -> List[Dict]:
        """Verified strategy using Firecrawl cloud scraping."""
        if not self.firecrawl_key:
            raise Exception("Firecrawl API key missing")
            
        url = f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}&children={children}&pets={pets}&price_max={budget_max}"
        
        async def make_firecrawl_call():
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "url": url, 
                    "formats": ["markdown"], 
                    "waitFor": 8000,
                    "actions": [
                        {"type": "scroll", "direction": "down", "amount": 500},
                        {"type": "wait", "milliseconds": 2000}
                    ]
                }
                return await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {self.firecrawl_key}"},
                    json=payload
                )

        response = await smart_requester.request(make_firecrawl_call)
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            markdown = data.get('markdown', '')
            
            if "dropped her ice cream" in markdown or "temporarily unavailable" in markdown:
                raise Exception("Airbnb blocked Firecrawl (503)")
                
            return self._parse_markdown(markdown, region, nights)
        else:
            raise Exception(f"Firecrawl API Error: {response.status_code}")

    def _get_fallback_data(self, region: str, nights: int, *args, **kwargs) -> List[Dict]:
        """Emergency fallback data when all scraping fails."""
        print(f"   ⚠️ Using fallback data for {region}")
        return [
            {
                "name": f"Gemütliches Haus in {region} (Fallback)",
                "location": region,
                "price_per_night": 120,
                "rating": 4.5,
                "reviews": 10,
                "pet_friendly": True,
                "source": "fallback",
                "url": "https://www.airbnb.com",
                "image_url": "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&q=80&w=720"
            }
        ]

    def _parse_markdown(self, text: str, region: str, searched_nights: int) -> List[Dict]:
        deals = []
        
        # 0. Check for "No results" or "Other dates" sections
        # If we see "Results for other dates", we should truncate the text to avoid parsing them
        other_dates_patterns = [
            "Results for other dates", "Ergebnisse für andere Daten",
            "Suggested results", "Vorgeschlagene Ergebnisse",
            "Try adjusting your search", "Versuche es mit anderen Filtern"
        ]
        
        clean_text = text
        for p in other_dates_patterns:
            if p in text:
                # Truncate text at the first occurrence of such a section
                clean_text = text.split(p)[0]
                break
        
        # 1. Identify all Room IDs and their positions in the CLEAN text
        id_pattern = re.compile(r'rooms/(\d+)')
        matches = [(m.group(1), m.start()) for m in id_pattern.finditer(clean_text)]
        
        # Deduplicate while preserving order of first appearance
        seen = set()
        unique_matches = []
        for rid, pos in matches:
            if rid not in seen:
                seen.add(rid)
                unique_matches.append((rid, pos))
        
        for i, (room_id, start_pos) in enumerate(unique_matches):
            # Define the text block for this listing
            # Start: from the first mention of this ID
            # End: until the start of the next ID (or reasonable limit)
            end_pos = unique_matches[i+1][1] if i + 1 < len(unique_matches) else len(clean_text)
            
            # Limit block size to avoid processing huge chunks if IDs are far apart
            # But typically the text follows the images
            block_len = min(end_pos - start_pos, 4000) 
            block = clean_text[start_pos:start_pos + block_len]
            
            # --- PARSING LOGIC ---
            
            # 1. Image
            image_url = ""
            # Look for the image associated with this ID in the block (or just before)
            # Re-scan the original text slightly before the start_pos to catch the image bracket
            img_match = re.search(r'!\[.*?\]\((https://[^)]+)\)', clean_text[max(0, start_pos-300):start_pos+300])
            if img_match:
                image_url = img_match.group(1).split('?')[0] + "?im_w=720"

            # 2. Name
            # Strategy: Look for the title which is often a bold line or a line following the "Apartment in..."
            name = "[DEBUG: NAME FEHLT]"
            
            # Remove image markdown from block to avoid noise
            clean_block = re.sub(r'!\[.*?\]\(.*?\)', '', block)
            lines = [l.strip() for l in clean_block.split('\n') if l.strip()]
            
            # Pattern for "Type in Location"
            type_pattern = r'(Apartment|Home|Condo|Villa|House|Guest suite|Cottage|Loft|Room|Private room) in ([A-Za-z\s,\-]+)'
            
            for idx, line in enumerate(lines):
                # If we find the type line, the name is usually the next line
                if re.search(type_pattern, line, re.I):
                    if idx + 1 < len(lines):
                        potential_name = lines[idx+1]
                        # Ensure it's not a rating line or another room ID
                        if "stars" not in potential_name.lower() and "rooms/" not in potential_name:
                            name = potential_name
                            break
                    # If it's the only line or next is invalid, use current minus the prefix
                    name = re.sub(type_pattern, '', line, flags=re.I).strip()
                    if not name: name = "Airbnb Stay"
                    break

            if name == "[DEBUG: NAME FEHLT]" or len(name) < 3:
                 # Fallback: Use the first non-link, non-rating line
                 for l in lines:
                     if "rooms/" not in l and "rating" not in l.lower() and "review" not in l.lower() and len(l) > 5:
                         name = l
                         break

            # Cleanup name: remove leading/trailing punctuation often found in markdown
            name = name.strip('*,# ')
            if name.lower() == region.lower(): # If name is just the city, it's a bad parse
                 name = f"Stay in {region}"

            # 3. Price
            price_per_night = 0
            # Search for "$1,350 ... for 5 nights" pattern
            # Matches: $1,234 or €1.234
            price_block_match = re.search(r'([\$\€\£])\s*([\d,\.]+).*?for\s+(\d+)\s+nights', block, re.DOTALL | re.IGNORECASE)
            
            if price_block_match:
                currency, amount_str, nights_found = price_block_match.groups()
                amount = int(re.sub(r'[^\d]', '', amount_str))
                nights_found = int(nights_found)
                if nights_found > 0:
                    price_per_night = round(amount / nights_found)
            else:
                # Fallback: Find any price and assume it is nightly if low, or total if high
                # Check for "per night" or "Nacht" nearby
                nightly_match = re.search(r'([\$\€\£])\s*([\d,\.]+)\s*(per night|night|Nacht)', block, re.IGNORECASE)
                if nightly_match:
                    price_per_night = int(re.sub(r'[^\d]', '', nightly_match.group(2)))
                else:
                    prices = re.findall(r'[\$\€\£]\s*([\d,\.]+)', block)
                    valid_prices = []
                    for p in prices:
                        try: 
                            v = int(re.sub(r'[^\d]', '', p))
                            valid_prices.append(v)
                        except: pass
                    
                    if valid_prices:
                        best_guess = min(valid_prices)
                        if best_guess > 1000:
                            price_per_night = round(best_guess / searched_nights)
                        else:
                            price_per_night = best_guess

            # 4. Rating / Reviews
            rating = 4.8
            reviews = 20
            # "4.32 out of 5 average rating, 141 reviews"
            rating_match = re.search(r'([\d\.]+)\s*out of 5', block)
            if rating_match:
                try: rating = float(rating_match.group(1))
                except: pass
            
            rev_match = re.search(r'(\d+)\s*reviews', block)
            if rev_match:
                try: reviews = int(rev_match.group(1))
                except: pass

            # Add to list
            # Availability logic: If no price could be determined, it's not a valid deal for these dates
            if price_per_night > 0:
                deals.append({
                    "name": name, 
                    "location": region, 
                    "price_per_night": price_per_night,
                    "rating": rating, 
                    "reviews": reviews, 
                    "pet_friendly": True,
                    "source": "airbnb (cloud)", 
                    "url": f"https://www.airbnb.com/rooms/{room_id}",
                    "image_url": image_url
                })
                
        return deals

SmartAirbnbScraper = PatchrightAirbnbScraper
