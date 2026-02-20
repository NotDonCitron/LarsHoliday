import httpx
import asyncio
import json

async def test_live_api():
    print("🚀 Starte Live-API Test (100% reale Daten Check)...")
    
    url = "http://localhost:8000/search"
    params = {
        "cities": "Zandvoort",
        "checkin": "2026-03-15",
        "checkout": "2026-03-22",
        "adults": 4,
        "pets": 1
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            print(f"📡 Sende Anfrage an API: {url} für Zandvoort...")
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                print(f"❌ API Fehler: Status {response.status_code}")
                return

            data = response.json()
            deals = data.get("top_10_deals", [])
            
            print(f"✅ API Antwort erhalten. Gefundene Deals: {len(deals)}")
            
            if not deals:
                print("⚠️ Keine Deals gefunden. (Möglicherweise blockiert oder keine Verfügbarkeit)")
                return

            for i, deal in enumerate(deals[:3], 1):
                name = deal.get('name', 'Unbekannt')
                source = deal.get('source', 'Unbekannt')
                price = deal.get('price_per_night', 0)
                deal_url = deal.get('url', '')
                image_url = deal.get('image_url', '')

                print(f"\n--- Deal #{i}: {name} ---")
                print(f"   Quelle: {source}")
                print(f"   Preis: €{price}/Nacht")
                
                # Check URL
                if "booking.com" in deal_url or "airbnb.com" in deal_url:
                    print(f"   ✅ URL Valid: {deal_url[:60]}...")
                else:
                    print(f"   ❌ URL UNGÜLTIG: {deal_url}")

                # Check Image
                if image_url and image_url.startswith('http'):
                    print(f"   ✅ Bild-URL vorhanden: {image_url[:60]}...")
                else:
                    print(f"   ❌ Bild-URL FEHLT oder ist Platzhalter")

        except Exception as e:
            print(f"❌ Test fehlgeschlagen: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_api())
