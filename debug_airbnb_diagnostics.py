import asyncio
import os
import httpx
from urllib.parse import quote
from patchright_airbnb_scraper import PatchrightAirbnbScraper

async def main():
    print("Starting Debug Search...")
    scraper = PatchrightAirbnbScraper()
    
    region = "Hamburg"
    checkin = "2026-02-15"
    checkout = "2026-02-22"
    adults = 4
    
    # Adding price_max to URL to verify it helps
    url = f"https://www.airbnb.com/s/{quote(region)}/homes?checkin={checkin}&checkout={checkout}&adults={adults}&price_max=500"
    print(f"Scraping URL: {url}")
    
    headers = {"Authorization": f"Bearer {scraper.firecrawl_key}"}
    
    print(f"Using Firecrawl Key: {scraper.firecrawl_key[:5]}...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers=headers,
                json={"url": url, "formats": ["markdown"], "waitFor": 5000}
            )
            
            if response.status_code == 200:
                markdown = response.json().get('data', {}).get('markdown', '')
                print(f"Received {len(markdown)} chars of markdown.")
                
                with open("debug_content.md", "w", encoding="utf-8") as f:
                    f.write(markdown)
                print("Saved raw markdown to debug_content.md")
                
                # Print snippet
                print("\n--- SNIPPET START ---")
                print(markdown[:1000])
                print("--- SNIPPET END ---\n")
                
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
