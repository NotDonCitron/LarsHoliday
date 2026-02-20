import asyncio
from holland_agent import VacationAgent

async def test_international():
    print("🌍 STARTING GLOBAL TEST: LONDON")
    agent = VacationAgent(budget_max=300)

    # Search for London, 2 Adults, 1 Dog
    results = await agent.find_best_deals(
        cities=["London"],
        checkin="2026-05-10",
        checkout="2026-05-12", # 2 nights
        group_size=2,
        pets=1
    )

    print("\n" + "="*50)
    print("🔍 DIAGNOSE-BERICHT")
    print("="*50)
    
    # Analyze Booking.com
    booking = [d for d in agent.all_deals if d['source'] == 'booking.com']
    print(f"\n🏨 Booking.com: {len(booking)} Treffer")
    if booking:
        first = booking[0]
        print(f"   Sample: {first['name']} - €{first['price_per_night']}")
        print(f"   Link: {first['url'][:60]}...")
        if "/hotel/" in first['url']:
            print("   ✅ Link-Check: OK")
        else:
            print("   ❌ Link-Check: FAIL (Such-Link?)")

    # Analyze Airbnb
    airbnb = [d for d in agent.all_deals if d['source'] == 'airbnb']
    print(f"\n🏡 Airbnb: {len(airbnb)} Treffer")
    if airbnb:
        first = airbnb[0]
        print(f"   Sample: {first['name']} - €{first['price_per_night']}")
        print(f"   Link: {first['url'][:60]}...")
        if "/rooms/" in first['url']:
            print("   ✅ Link-Check: OK")
        else:
            print("   ❌ Link-Check: FAIL (Fallback?)")

    # Summary Check
    if len(booking) > 0 and len(airbnb) > 0:
        print("\n✅ GLOBAL TEST BESTANDEN: Daten aus beiden Quellen erhalten.")
    else:
        print("\n⚠️ WARNUNG: Eine oder mehrere Quellen leer.")

if __name__ == "__main__":
    asyncio.run(test_international())
