import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from holland_agent import VacationAgent
from gui_app import VacationApp

# Subclass only to avoid launching the full Tkinter GUI window
class HeadlessApp(VacationApp):
    def __init__(self):
        # Skip UI init
        pass

async def test_gui_workflow():
    print("🚀 SIMULATION: User types 'Vienna' in GUI...")
    
    agent = VacationAgent(budget_max=200)
    
    # 1. Simulate Search (Short dummy search to save API calls/Time)
    # We create a dummy result manually to test HTML generation specifically
    results = {
        'search_params': {
            'cities': ['Vienna'],
            'checkin': '2026-05-01',
            'checkout': '2026-05-03',
            'nights': 2,
            'group_size': 2,
            'pets': 0
        },
        'top_10_deals': [
            {
                'name': 'Test Hotel Vienna',
                'location': 'Vienna City Center',
                'rating': 4.8,
                'reviews': 120,
                'source': 'booking.com',
                'price_per_night': 150,
                'url': 'https://booking.com/hotel/vienna-test'
            },
            {
                'name': 'Cozy Vienna Apartment',
                'location': 'Leopoldstadt',
                'rating': 4.9,
                'reviews': 85,
                'source': 'airbnb',
                'price_per_night': 110,
                'url': 'https://airbnb.com/rooms/12345'
            }
        ]
    }
    
    print("🎨 Generating HTML Report with REAL logic...")
    
    # 2. Use REAL Report Logic
    app = HeadlessApp()
    app._generate_html_report(results)
    
    # 3. Verify HTML Content
    if os.path.exists("last_search_report.html"):
        file_size = os.path.getsize("last_search_report.html")
        print(f"📦 File Size: {file_size} bytes ({file_size/1024:.1f} KB)")
        
        with open("last_search_report.html", "r", encoding="utf-8") as f:
            content = f.read()
            
        print("\n🔍 VERIFYING HTML CONTENT:")
        if "📊 Deine Urlaubs-Deals" in content:
            print("   ✅ CSS/Layout found (Header present).")
        else:
            print("   ❌ Header MISSING (Still using mock?)")
            
        if "Vienna City Center" in content:
             print("   ✅ Test Data found.")
             
    else:
        print("❌ Report file was NOT created.")

if __name__ == "__main__":
    asyncio.run(test_gui_workflow())

