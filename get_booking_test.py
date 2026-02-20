import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def fetch_booking_data():
    key = os.getenv("FIRECRAWL_API_KEY")
    # Suche für Zandvoort
    url = "https://www.booking.com/searchresults.html?ss=Zandvoort&checkin=2026-03-15&checkout=2026-03-22&group_adults=4&no_rooms=1&nflt=ht_id%3D220%3Bhotelfacility%3D14"
    
    print(f"📡 Hole echte Booking-Daten von Firecrawl...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {key}"},
            json={"url": url, "formats": ["html"], "waitFor": 5000}
        )
        if response.status_code == 200:
            html = response.json().get('data', {}).get('html', '')
            with open("debug_booking.html", "w") as f:
                f.write(html)
            print(f"✅ Booking-Daten gespeichert (debug_booking.html, {len(html)} Zeichen)")
        else:
            print(f"❌ Fehler: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(fetch_booking_data())
