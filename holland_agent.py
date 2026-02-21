"""
Vacation Deal Finder Agent - Main Orchestrator
AI-powered vacation deal finder for any destination
Finds budget-friendly, dog-friendly accommodations

Key improvements:
- Parallel cross-source scraping (Booking + Airbnb simultaneously)
- Parallel cross-city scraping with staggered start times
- Health reporting after search
"""

import asyncio
import json
import random
import os
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv  # pyre-ignore[21]

from booking_scraper import BookingScraper  # pyre-ignore[21]
from patchright_airbnb_scraper import PatchrightAirbnbScraper as SmartAirbnbScraper # Use verified version
from weather_integration import WeatherIntegration  # pyre-ignore[21]
from deal_ranker import DealRanker  # pyre-ignore[21]
from scraper_health import health_reporter  # pyre-ignore[21]

load_dotenv()

class VacationAgent:
    """
    Main agent that orchestrates vacation deal search across multiple sources
    """

    def __init__(self, budget_min: int = 40, budget_max: int = 250):
        self.budget_min = budget_min
        self.budget_max = budget_max
        self.booking_scraper = BookingScraper()
        self.airbnb_scraper = SmartAirbnbScraper()
        self.weather = WeatherIntegration()
        # Explicitly set API Key for weather if needed
        if not os.getenv("OPENWEATHER_API_KEY"):
             print("   ⚠️ WARNUNG: OPENWEATHER_API_KEY fehlt in Umgebungsvariablen!")
        self.ranker = DealRanker(budget_max=budget_max)
        self.all_deals = []

    async def find_best_deals(
        self,
        cities: List[str],
        checkin: str,
        checkout: str,
        group_size: int = 4,
        children: int = 0,
        pets: int = 1,
        budget: int = 250,
        budget_type: str = "night"
    ) -> Dict:
        """
        Main method - finds and ranks vacation deals
        """
        # Calculate nights
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = max(1, (d2 - d1).days)

        # Budget calculation
        if budget_type == "total":
            self.budget_max = round(budget / nights)
        else:
            self.budget_max = budget
        
        self.ranker.budget_max = self.budget_max

        print(f"\n🤖 Vacation Deal Finder")
        print(f"   Destinations: {', '.join(cities)}")
        print(f"   Dates: {checkin} → {checkout} ({nights} nights)")
        print(f"   Group: {group_size} adults, {children} children, {pets} dog(s)")
        print(f"   Budget: €{self.budget_max}/night (Calculated from {budget} {budget_type})\n")

        # Start search across all cities with staggered parallel scraping
        print("🔍 Searching accommodations...")
        
        async def _search_with_delay(city: str, delay: float):
            """Search a city with initial delay for stagger."""
            if delay > 0:
                await asyncio.sleep(delay)
            return await self._search_single_city(
                city, checkin, checkout, nights, group_size, children, pets
            )
        
        # Stagger cities by 2s to avoid thundering herd
        tasks = [
            _search_with_delay(city, i * 2.0)
            for i, city in enumerate(cities)
        ]
        results_per_city = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions from individual city searches
        results_per_city = [
            r if isinstance(r, list) else []
            for r in results_per_city
        ]

        # Aggregate all deals
        self.all_deals = []
        for deals_list in results_per_city:
            self.all_deals.extend(deals_list)

        # Validate deals (e.g., price and pet-friendly enforcement)
        self._validate_deals(pets)

        print(f"   Found {len(self.all_deals)} valid properties\n")

        # Enrich with weather data
        print("🌤️  Fetching weather forecasts...")
        self.all_deals = await self.weather.enrich_deals_with_weather(
            self.all_deals, cities
        )

        # Rank deals
        print("📊 Ranking deals...\n")
        ranked = self.ranker.rank_deals(self.all_deals, nights)

        # Separate deals by source
        airbnb_deals = [d for d in ranked if "airbnb" in d.get("source", "").lower()]
        booking_deals = [d for d in ranked if "booking" in d.get("source", "").lower()]

        # Generate summary
        summary = self.ranker.generate_summary(ranked, nights)

        # Print scraper health report
        print(health_reporter.generate())

        return {
            "timestamp": datetime.now().isoformat(),
            "search_params": {
                "cities": cities,
                "checkin": checkin,
                "checkout": checkout,
                "nights": nights,
                "group_size": group_size,
                "pets": pets,
                "budget_range": f"€{self.budget_min}-{self.budget_max}"
            },
            "total_deals_found": len(self.all_deals),
            "top_airbnb_deals": airbnb_deals[:15],
            "top_booking_deals": booking_deals[:15],
            "top_10_deals": ranked[:10], # Keep for backward compatibility
            "summary": summary
        }

    def _validate_deals(self, pets: int):
        """
        Validate and filter aggregated deals based on requirements
        """
        # 1. Basic Availability Check: Must have a price
        self.all_deals = [
            deal for deal in self.all_deals 
            if deal.get('price_per_night', 0) > 0
        ]

        # 2. Requirement Check: Pets
        if pets > 0:
            # Filter only pet-friendly properties
            self.all_deals = [
                deal for deal in self.all_deals 
                if deal.get('pet_friendly') is True
            ]

    async def _search_single_city(
        self,
        city: str,
        checkin: str,
        checkout: str,
        nights: int,
        group_size: int,
        children: int,
        pets: int
    ) -> List[Dict]:
        """
        Search all sources for a single city/region
        """
        deals = []

        # Parallel search: Booking.com + Airbnb concurrently
        async def _search_booking():
            try:
                # Passing budget_max to scraper if supported (will update scraper next)
                return await self.booking_scraper.search_booking(
                    city, checkin, checkout, group_size, children
                )
            except Exception as e:
                print(f"   Warning: Booking.com search failed for {city}: {e}")
                return []

        async def _search_airbnb():
            try:
                # Passing budget_max and children to airbnb scraper
                return await self.airbnb_scraper.search_airbnb(
                    city, checkin, checkout, group_size, children, pets, self.budget_max
                )
            except Exception as e:
                print(f"   Warning: Airbnb search failed for {city}: {e}")
                return []

        booking_deals, airbnb_deals = await asyncio.gather(
            _search_booking(),
            _search_airbnb()
        )
        
        deals.extend(booking_deals)  # pyre-ignore[6]
        deals.extend(airbnb_deals)  # pyre-ignore[6]

        # Add Center Parcs data (if relevant for location)
        center_parcs_deals = self._get_center_parcs_data(city)
        deals.extend(center_parcs_deals)

        return deals

    def _get_center_parcs_data(self, city: str) -> List[Dict]:
        """
        TODO: Implement real Center Parcs scraping.
        Returning empty list for now to ensure 100% real scraped data from other sources.
        """
        return []

    async def cleanup(self):
        """Clean up browser sessions"""
        try:
            if hasattr(self.airbnb_scraper, 'close'):
                await self.airbnb_scraper.close()
        except Exception:
            pass
        try:
            if hasattr(self.booking_scraper, 'close'):
                await self.booking_scraper.close()
        except Exception:
            pass

# Backward compatibility alias
HollandVacationAgent = VacationAgent


async def main():
    """Example usage"""
    agent = VacationAgent(budget_min=40, budget_max=250)

    try:
        results = await agent.find_best_deals(
            cities=["Amsterdam", "Berlin", "Antwerp"],
            checkin="2026-02-15",
            checkout="2026-02-22",
            group_size=4,
            pets=1
        )

        # Print results as JSON
        print("\n" + "="*60)
        print("RESULTS")
        print("="*60 + "\n")
        print(json.dumps(results, indent=2, ensure_ascii=False))

    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
