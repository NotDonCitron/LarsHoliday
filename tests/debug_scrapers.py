import asyncio
import logging
import json
import sys
import os

# Ensure the project root is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from booking_scraper import BookingScraper
from airbnb_scraper import AirbnbScraper

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def debug_booking():
    print("\n--- Debugging Booking.com Scraper ---")
    scraper = BookingScraper()
    try:
        # Search parameters
        city = "Amsterdam"
        checkin = "2026-03-01"
        checkout = "2026-03-08"
        adults = 4
        
        print(f"Searching {city} for {adults} adults from {checkin} to {checkout}...")
        results = await scraper.search_booking(city, checkin, checkout, adults)
        
        print(f"Found {len(results)} results.")
        for i, deal in enumerate(results[:3]):
            print(f"\nResult #{i+1}:")
            print(json.dumps(deal, indent=2))
            
    except Exception as e:
        print(f"Error debugging Booking.com: {e}")

async def debug_airbnb():
    print("\n--- Debugging Airbnb Scraper ---")
    scraper = AirbnbScraper()
    try:
        # Search parameters
        region = "Amsterdam"
        checkin = "2026-03-01"
        checkout = "2026-03-08"
        adults = 4
        
        print(f"Searching {region} for {adults} adults from {checkin} to {checkout}...")
        results = await scraper.search_airbnb(region, checkin, checkout, adults)
        
        print(f"Found {len(results)} results.")
        for i, deal in enumerate(results[:3]):
            print(f"\nResult #{i+1}:")
            print(json.dumps(deal, indent=2))
            
    except Exception as e:
        print(f"Error debugging Airbnb: {e}")

async def main():
    await debug_booking()
    await debug_airbnb()

if __name__ == "__main__":
    asyncio.run(main())
