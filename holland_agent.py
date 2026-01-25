"""
Holland Vacation Agent - Main Orchestrator
AI-powered vacation deal finder for Netherlands
Finds budget-friendly, dog-friendly accommodations
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

from booking_scraper import BookingScraper
from airbnb_scraper import AirbnbScraper
from weather_integration import WeatherIntegration
from deal_ranker import DealRanker

load_dotenv()


class HollandVacationAgent:
    """
    Main agent that orchestrates vacation deal search across multiple sources
    """

    def __init__(self, budget_min: int = 40, budget_max: int = 250):
        self.budget_min = budget_min
        self.budget_max = budget_max
        self.booking_scraper = BookingScraper()
        self.airbnb_scraper = AirbnbScraper()
        self.weather = WeatherIntegration()
        self.ranker = DealRanker(budget_max=budget_max)
        self.all_deals = []

    async def find_best_deals(
        self,
        cities: List[str],
        checkin: str,
        checkout: str,
        group_size: int = 4,
        pets: int = 1
    ) -> Dict:
        """
        Main method - finds and ranks vacation deals

        Args:
            cities: List of city names (e.g., ["Amsterdam", "Rotterdam"])
            checkin: Check-in date (YYYY-MM-DD)
            checkout: Check-out date (YYYY-MM-DD)
            group_size: Number of adults
            pets: Number of pets

        Returns:
            Dictionary with search results, ranked deals, and summary
        """
        print(f"\n🤖 Holland Vacation Deal Finder")
        print(f"   Cities: {', '.join(cities)}")
        print(f"   Dates: {checkin} → {checkout}")
        print(f"   Group: {group_size} adults + {pets} dog(s)")
        print(f"   Budget: €{self.budget_min}-{self.budget_max}/night\n")

        # Calculate nights
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
        nights = (d2 - d1).days

        # Start parallel search across all cities
        print("🔍 Searching accommodations...")
        tasks = []
        for city in cities:
            tasks.append(
                self._search_single_city(
                    city, checkin, checkout, nights, group_size, pets
                )
            )

        results_per_city = await asyncio.gather(*tasks)

        # Aggregate all deals
        self.all_deals = []
        for deals_list in results_per_city:
            self.all_deals.extend(deals_list)

        print(f"   Found {len(self.all_deals)} properties\n")

        # Enrich with weather data
        print("🌤️  Fetching weather forecasts...")
        self.all_deals = await self.weather.enrich_deals_with_weather(
            self.all_deals, cities
        )

        # Rank deals
        print("📊 Ranking deals...\n")
        ranked = self.ranker.rank_deals(self.all_deals, nights)

        # Generate summary
        summary = self.ranker.generate_summary(ranked, nights)

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
            "top_10_deals": ranked[:10],
            "summary": summary
        }

    async def _search_single_city(
        self,
        city: str,
        checkin: str,
        checkout: str,
        nights: int,
        group_size: int,
        pets: int
    ) -> List[Dict]:
        """
        Search all sources for a single city

        Args:
            city: City name
            checkin: Check-in date
            checkout: Check-out date
            nights: Number of nights
            group_size: Number of adults
            pets: Number of pets

        Returns:
            List of deals from all sources
        """
        deals = []

        # Search Booking.com
        try:
            booking_deals = await self.booking_scraper.search_booking(
                city, checkin, checkout, group_size
            )
            deals.extend(booking_deals)
        except Exception as e:
            print(f"   Warning: Booking.com search failed for {city}: {e}")

        # Search Airbnb
        try:
            airbnb_deals = await self.airbnb_scraper.search_airbnb(
                city, checkin, checkout, group_size
            )
            deals.extend(airbnb_deals)
        except Exception as e:
            print(f"   Warning: Airbnb search failed for {city}: {e}")

        # Add Center Parcs static data
        center_parcs_deals = self._get_center_parcs_data(city)
        deals.extend(center_parcs_deals)

        return deals

    def _get_center_parcs_data(self, city: str) -> List[Dict]:
        """
        Get static Center Parcs data for Netherlands

        Center Parcs are popular dog-friendly vacation parks in Netherlands
        """
        all_parks = [
            {
                "name": "Center Parcs De Kempervennen",
                "location": "Westerhoven, North Brabant",
                "price_per_night": 45,
                "rating": 4.2,
                "reviews": 234,
                "pet_friendly": True,
                "source": "center-parcs",
                "url": "https://www.centerparcs.nl/nl-nl/nederland/fp_VK_vakantiepark-de-kempervennen"
            },
            {
                "name": "Center Parcs Zandvoort Beach",
                "location": "Zandvoort aan Zee",
                "price_per_night": 58,
                "rating": 4.5,
                "reviews": 512,
                "pet_friendly": True,
                "source": "center-parcs",
                "url": "https://www.centerparcs.nl/nl-nl/nederland/fp_PZ_vakantiepark-zandvoort"
            },
            {
                "name": "Center Parcs De Huttenheugte",
                "location": "Dalen, Drenthe",
                "price_per_night": 42,
                "rating": 4.1,
                "reviews": 189,
                "pet_friendly": True,
                "source": "center-parcs",
                "url": "https://www.centerparcs.nl/nl-nl/nederland/fp_DH_vakantiepark-de-huttenheugte"
            },
            {
                "name": "Center Parcs Port Zélande",
                "location": "Ouddorp, Zeeland",
                "price_per_night": 52,
                "rating": 4.4,
                "reviews": 423,
                "pet_friendly": True,
                "source": "center-parcs",
                "url": "https://www.centerparcs.nl/nl-nl/nederland/fp_PZ_vakantiepark-port-zelande"
            },
            {
                "name": "Center Parcs Het Heijderbos",
                "location": "Heijen, Limburg",
                "price_per_night": 48,
                "rating": 4.3,
                "reviews": 367,
                "pet_friendly": True,
                "source": "center-parcs",
                "url": "https://www.centerparcs.nl/nl-nl/nederland/fp_HB_vakantiepark-het-heijderbos"
            }
        ]

        # Return all parks (they're spread across Netherlands)
        return all_parks

    def cleanup(self):
        """Clean up browser sessions"""
        try:
            self.booking_scraper.close_session()
            self.airbnb_scraper.close_session()
        except Exception:
            pass


async def main():
    """Example usage"""
    agent = HollandVacationAgent(budget_min=40, budget_max=250)

    try:
        results = await agent.find_best_deals(
            cities=["Amsterdam", "Rotterdam", "Zandvoort"],
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
        agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
