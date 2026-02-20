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
        # Add price_max to filter out luxury villas and ensure better budget fit
        # Assume a max budget per night of ~300 to be safe, or use the budget_max if passed (defaulting to 500 here to be safe)
        url = f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}&price_max=600"
        
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

    def _parse_markdown(self, text: str, region: str, searched_nights: int) -> List[Dict]:
        deals = []
        # 1. Identify all Room IDs and their positions
        # format: https://www.airbnb.com/rooms/123456...
        id_pattern = re.compile(r'rooms/(\d+)')
        matches = [(m.group(1), m.start()) for m in id_pattern.finditer(text)]
        
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
            end_pos = unique_matches[i+1][1] if i + 1 < len(unique_matches) else len(text)
            
            # Limit block size to avoid processing huge chunks if IDs are far apart
            # But typically the text follows the images
            block_len = min(end_pos - start_pos, 4000) 
            block = text[start_pos:start_pos + block_len]
            
            # --- PARSING LOGIC ---
            
            # 1. Image
            image_url = ""
            # Look for the image associated with this ID in the block (or just before)
            # Actually, the block starts at the URL in the markdown link: [![]()]...
            # We want the image *inside* the markdown link that contains the room_id
            # Re-scan the original text slightly before the start_pos to catch the image bracket
            # But simpler: scan the block for image syntax
            img_match = re.search(r'!\[.*?\]\((https://[^)]+)\)', text[max(0, start_pos-300):start_pos+300])
            if img_match:
                image_url = img_match.group(1).split('?')[0] + "?im_w=720"

            # 2. Name
            # Strategy: Look for "Apartment in...", "Home in..." and take the next line
            name = "[DEBUG: NAME FEHLT]"
            
            # Common prefixes in Airbnb listings
            type_match = re.search(r'(Apartment|Home|Condo|Villa|House|Guest suite|Cottage|Loft) in [A-Za-z\s]+', block)
            if type_match:
                # The title is usually the line AFTER the type description
                # Split block by lines and find the index
                lines = block.split('\n')
                for idx, line in enumerate(lines):
                    if type_match.group(0) in line:
                        # Check next non-empty line
                        if idx + 1 < len(lines):
                            potential_name = lines[idx+1].strip()
                            if potential_name and len(potential_name) > 3:
                                name = potential_name
                                break
                        # Sometimes it's the same line?
                        if name == "[DEBUG: NAME FEHLT]":
                             name = line.replace(type_match.group(0), "").strip()

            if name == "[DEBUG: NAME FEHLT]" or len(name) < 5:
                 # Fallback: Look for "Guest favorite" and take line after?
                 # Or use the first generic text line
                 lines = [l.strip() for l in block.split('\n') if len(l.strip()) > 10 and "rooms/" not in l and "Review" not in l]
                 if lines: name = lines[0] # Very rough fallback

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
                prices = re.findall(r'[\$\€\£]\s*([\d,\.]+)', block)
                valid_prices = []
                for p in prices:
                    try: 
                        v = int(re.sub(r'[^\d]', '', p))
                        valid_prices.append(v)
                    except: pass
                
                if valid_prices:
                    # Sort logic
                    best_guess = min(valid_prices)
                    # If the best guess is super high (e.g. > 1000), treat as total
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
