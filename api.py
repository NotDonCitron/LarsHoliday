from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
from holland_agent import HollandVacationAgent
import uvicorn
import asyncio
import os

app = FastAPI(title="Lars Holiday Deal API")

# Allow requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = HollandVacationAgent()

def get_env_robust(key_name):
    # Try exact match
    val = os.getenv(key_name)
    if val: return val
    # Try lowercase/uppercase
    for k, v in os.environ.items():
        if k.upper().strip() == key_name.upper():
            return v
    return None

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "keys_found": {
            "OPENWEATHER_API_KEY": bool(get_env_robust("OPENWEATHER_API_KEY")),
            "FIRECRAWL_API_KEY": bool(get_env_robust("FIRECRAWL_API_KEY")),
            "AGENT_BROWSER_SESSION": bool(get_env_robust("AGENT_BROWSER_SESSION"))
        },
        "available_vars": [k for k in os.environ.keys() if "API" in k or "KEY" in k],
        "python_version": os.sys.version
    }

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend_dashboard.html")

@app.get("/search")
async def search_deals(
    cities: str = Query(..., description="Comma-separated list of cities"),
    checkin: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    checkout: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    adults: int = 4,
    children: int = 0,
    pets: int = 1,
    budget: int = 250,
    budget_type: str = "night"
):
    print(f"\n--- [API Request] Suche gestartet: {cities} ---")
    city_list = [c.strip() for c in cities.split(",")]
    
    # Run the existing agent logic
    print(f"--- [API Request] Agent findet Deals für {len(city_list)} Städte...")
    results = await agent.find_best_deals(
        cities=city_list,
        checkin=checkin,
        checkout=checkout,
        group_size=adults,
        children=children,
        pets=pets,
        budget=budget,
        budget_type=budget_type
    )
    print(f"--- [API Request] Agent fertig. {results.get('total_deals_found')} Deals gefunden.")
    
    # Process all deal lists for image fallbacks
    for key in ["top_10_deals", "top_airbnb_deals", "top_booking_deals"]:
        deals = results.get(key, [])
        for deal in deals:
            if not deal.get("image_url"):
                deal["image_url"] = "https://via.placeholder.com/800x450.png?text=KEIN+BILD+GEFUNDEN"
        results[key] = deals
        
    return results

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
