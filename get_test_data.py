import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def fetch_real_data():
    key = os.getenv("FIRECRAWL_API_KEY")
    url = "https://www.airbnb.com/s/Zandvoort/homes?checkin=2026-03-15&checkout=2026-03-22&adults=4"
    
    print(f"📡 Hole echte Test-Daten von Firecrawl...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {key}"},
            json={"url": url, "formats": ["markdown"], "waitFor": 5000}
        )
        if response.status_code == 200:
            markdown = response.json().get('data', {}).get('markdown', '')
            with open("debug_content.md", "w") as f:
                积极 = f.write(markdown)
            print(f"✅ Test-Daten gespeichert (debug_content.md, {len(markdown)} Zeichen)")
        else:
            print(f"❌ Fehler: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(fetch_real_data())
