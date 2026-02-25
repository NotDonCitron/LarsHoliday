import asyncio
import os
import re
import httpx
from booking_scraper import BookingScraper
from dotenv import load_dotenv
from bs4 import BeautifulSoup

async def debug_booking_images():
    load_dotenv()
    scraper = BookingScraper()
    city = "Amsterdam"
    checkin = "2026-03-08"
    checkout = "2026-03-15"
    
    url = scraper._build_booking_url(city, checkin, checkout, 2, 0)
    
    async with httpx.AsyncClient(timeout=150.0) as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}"},
            json={"url": url, "formats": ["html"], "waitFor": 10000}
        )
        
        if response.status_code == 200:
            html = response.json().get('data', {}).get('html', '')
            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.find_all('div', {'data-testid': 'property-card'})
            
            for i, card in enumerate(cards[:3]):
                imgs = card.find_all('img')
                print(f"Card {i} has {len(imgs)} images.")
                for img in imgs:
                    print(f"  - {img.get('src', '')[:50]}...")
        else:
            print(f"Error: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(debug_booking_images())
