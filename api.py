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
    pets: int = 1
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
        pets=pets
    )
    print(f"--- [API Request] Agent fertig. {results.get('total_deals_found')} Deals gefunden.")
    
    # Vibe Polish: Ensure every deal has an image with high variety
    fallback_images = [
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1473116763249-2faaef81ccda?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?auto=format&fit=crop&w=800&q=80"
    ]
    
    final_deals = []
    for i, deal in enumerate(results.get("top_10_deals", [])):
        # STRENGE VALIDIERUNG: Nur Deals mit Preis und Link
        if deal.get("price_per_night", 0) > 0 and deal.get("url"):
            if not deal.get("image_url") or len(deal["image_url"]) < 5:
                image_idx = (hash(deal.get("name", "deal")) + i) % len(fallback_images)
                deal["image_url"] = fallback_images[image_idx]
            final_deals.append(deal)
    
    results["top_10_deals"] = final_deals
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
