from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional, Dict
from pydantic import BaseModel
from fastapi.responses import FileResponse, StreamingResponse
from holland_agent import HollandVacationAgent
from report_generator import ReportGenerator
import uvicorn
import asyncio
import os
import io

class ExportRequest(BaseModel):
    deals: List[Dict]
    search_params: Dict

app = FastAPI(title="Lars Holiday Deal API")
report_gen = ReportGenerator()
agent = HollandVacationAgent()

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

@app.post("/export-pdf")
async def export_pdf(request: ExportRequest):
    print(f"--- [API Request] PDF Export gestartet für {len(request.deals)} Deals ---")
    
    # Create temp filename
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        filename = tmp.name
    
    success = report_gen.generate_report(
        deals=request.deals,
        search_params=request.search_params,
        filename=filename
    )
    
    if success:
        return FileResponse(
            filename, 
            media_type="application/pdf", 
            filename="UrlaubsDeals.pdf",
            background=None # FileResponse handles cleanup if we use a background task but let's keep it simple
        )
    return {"error": "PDF generation failed"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
