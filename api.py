from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from holland_agent import HollandVacationAgent
import uvicorn
import asyncio

app = FastAPI(title="Lars Holiday Deal API")

# Allow requests from our future React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = HollandVacationAgent()

@app.get("/")
async def root():
    return {"message": "Welcome to Lars Holiday Deal API", "status": "online"}

@app.get("/search")
async def search_deals(
    cities: str = Query(..., description="Comma-separated list of cities"),
    checkin: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    checkout: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    adults: int = 4,
    pets: int = 1
):
    city_list = [c.strip() for c in cities.split(",")]
    
    # Run the existing agent logic
    results = await agent.find_best_deals(
        cities=city_list,
        checkin=checkin,
        checkout=checkout,
        group_size=adults,
        pets=pets
    )
    
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
