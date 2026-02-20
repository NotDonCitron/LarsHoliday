"""
Weather Integration Module for Holland Vacation Agent
Uses OpenWeather API to fetch forecasts and enhance deal ranking
"""

import httpx
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class APICache:
    """Simple cache with TTL for API responses"""

    def __init__(self, ttl_minutes: int = 10):
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache = {}

    def get(self, key: str) -> Optional[Dict]:
        """Retrieve cached data if not expired"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return data
        return None

    def set(self, key: str, value: Dict):
        """Store data with current timestamp"""
        self.cache[key] = (value, datetime.now())


def get_env_robust(key_name):
    val = os.getenv(key_name)
    if val: return val
    for k, v in os.environ.items():
        if k.upper().strip() == key_name.upper():
            return v
    return None

class WeatherIntegration:
    """Handles weather API calls and caching"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_env_robust("OPENWEATHER_API_KEY")
        self.cache = APICache(ttl_minutes=10)
        self.base_url = "https://api.openweathermap.org/data/2.5/forecast"

    async def get_weather_forecast(self, city: str) -> Dict:
        """
        Fetch 5-day weather forecast for a city/region

        Args:
            city: City or region name (e.g., "Amsterdam", "Berlin")

        Returns:
            Dict with city, forecast data, and average temperature
        """
        cache_key = f"weather_{city}"
        cached = self.cache.get(cache_key)

        if cached:
            return cached

        # Search for the city globally (removing hardcoded ,NL)
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",  # Celsius
            "lang": "en"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                    timeout=15.0
                )
                response.raise_for_status()
                weather_data = response.json()

            result = {
                "city": city,
                "forecast": weather_data.get("list", [])[:8],  # Next 5 days
                "avg_temp": self._calculate_avg_temp(weather_data),
                "conditions": self._get_weather_summary(weather_data)
            }

            self.cache.set(cache_key, result)
            return result

        except Exception as e:
            print(f"   Warning: Weather API error for {city}: {e}")
            return {
                "city": city,
                "forecast": [],
                "avg_temp": None,
                "conditions": "unavailable"
            }

    def _calculate_avg_temp(self, data: Dict) -> Optional[float]:
        """Calculate average temperature from forecast data"""
        temps = [item["main"]["temp"] for item in data.get("list", [])]
        return round(sum(temps) / len(temps), 1) if temps else None

    def _get_weather_summary(self, data: Dict) -> str:
        """Get general weather condition summary"""
        conditions = [item["weather"][0]["main"] for item in data.get("list", [])]
        if not conditions:
            return "unknown"

        # Most common condition
        most_common = max(set(conditions), key=conditions.count)
        return most_common.lower()

    async def enrich_deals_with_weather(self, deals: List[Dict], cities: List[str]) -> List[Dict]:
        """
        Add weather data and bonus to deals

        Args:
            deals: List of deal dictionaries
            cities: List of cities to fetch weather for

        Returns:
            Enriched deals with weather data and bonus multiplier
        """
        # Fetch weather for all cities
        weather_map = {}
        for city in cities:
            weather = await self.get_weather_forecast(city)
            weather_map[city.lower()] = weather

        # Enrich each deal
        for deal in deals:
            location = deal.get("location", "").split(",")[0].strip().lower()

            # Find matching weather data
            weather = None
            for city_key, city_weather in weather_map.items():
                if city_key in location or location in city_key:
                    weather = city_weather
                    break

            if weather and weather["avg_temp"]:
                deal["weather_forecast"] = weather

                # Weather bonus: 1.2x if average temp > 15°C
                if weather["avg_temp"] > 15:
                    deal["weather_bonus"] = 1.2
                else:
                    deal["weather_bonus"] = 1.0
            else:
                deal["weather_bonus"] = 1.0
                deal["weather_forecast"] = None

        return deals
