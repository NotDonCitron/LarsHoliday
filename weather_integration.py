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
            Dict with city, forecast data, and detailed weather information
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

        if not self.api_key:
            return self._get_error_response(city, "Missing API Key")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                    timeout=15.0
                )
                if response.status_code == 401:
                    return self._get_error_response(city, "Invalid API Key")
                response.raise_for_status()
                weather_data = response.json()

            # Extract detailed forecast data
            forecast_list = weather_data.get("list", [])
            
            # Process daily forecasts (every 8th entry = 1 day)
            daily_forecasts = []
            for i in range(0, min(40, len(forecast_list)), 8):
                if i < len(forecast_list):
                    item = forecast_list[i]
                    main = item.get("main", {})
                    wind = item.get("wind", {})
                    weather = item.get("weather", [{}])
                    
                    daily_forecasts.append({
                        "date": item.get("dt_txt", "").split(" ")[0],
                        "temp": round(float(main.get("temp", 0)), 1),
                        "temp_min": round(float(main.get("temp_min", 0)), 1),
                        "temp_max": round(float(main.get("temp_max", 0)), 1),
                        "humidity": main.get("humidity", 0),
                        "weather": weather[0].get("main", "Unknown") if weather else "Unknown",
                        "weather_description": weather[0].get("description", "") if weather else "",
                        "weather_icon": weather[0].get("icon", "01d") if weather else "01d",
                        "wind_speed": round(float(wind.get("speed", 0)) * 3.6, 1),  # m/s to km/h
                        "rain_probability": round(float(item.get("pop", 0)) * 100),  # Probability of precipitation %
                        "rain_mm": round(float(item.get("rain", {}).get("3h", 0)), 1),
                        "uv_index": self._estimate_uv_index(item),
                    })

            # Calculate detailed averages
            avg_temp = self._calculate_avg_temp(weather_data)
            avg_humidity = sum(f["humidity"] for f in daily_forecasts) / len(daily_forecasts) if daily_forecasts else 0
            avg_wind = sum(f["wind_speed"] for f in daily_forecasts) / len(daily_forecasts) if daily_forecasts else 0
            max_rain_prob = max((f["rain_probability"] for f in daily_forecasts), default=0)
            
            # Calculate activity scores
            activity_scores = self._calculate_activity_scores(daily_forecasts, avg_temp)

            result = {
                "city": city,
                "forecast": daily_forecasts,
                "avg_temp": avg_temp,
                "avg_humidity": round(avg_humidity, 1),
                "avg_wind_speed": round(avg_wind, 1),
                "max_rain_probability": max_rain_prob,
                "conditions": self._get_weather_summary(weather_data),
                "activity_scores": activity_scores,
                "weather_alert": self._check_weather_alert(daily_forecasts),
            }

            self.cache.set(cache_key, result)
            return result

        except Exception as e:
            print(f"   Warning: Weather API error for {city}: {e}")
            return self._get_error_response(city, str(e))

    def _get_error_response(self, city: str, error_msg: str) -> Dict:
        return {
            "city": city,
            "forecast": [],
            "avg_temp": None,
            "avg_humidity": None,
            "avg_wind_speed": None,
            "max_rain_probability": 0,
            "conditions": "unavailable",
            "error": error_msg,
            "activity_scores": {
                "beach": 0,
                "hiking": 0,
                "dog_walk": 0,
                "cycling": 0
            },
            "weather_alert": None
        }

    def _calculate_avg_temp(self, data: Dict) -> Optional[float]:
        """Calculate average temperature from forecast data"""
        list_data = data.get("list", [])
        if not list_data:
            return None
        temps = [item.get("main", {}).get("temp") for item in list_data if item.get("main", {}).get("temp") is not None]
        return round(sum(temps) / len(temps), 1) if temps else None

    def _get_weather_summary(self, data: Dict) -> str:
        """Get general weather condition summary"""
        conditions = [item["weather"][0]["main"] for item in data.get("list", [])]
        if not conditions:
            return "unknown"

        # Most common condition
        most_common = max(set(conditions), key=conditions.count)
        return most_common.lower()

    def _estimate_uv_index(self, item: Dict) -> int:
        """
        Estimate UV index based on weather conditions and time
        This is an approximation as OpenWeather free API doesn't provide UV
        """
        weather = item.get("weather", [{}])[0].get("main", "").lower()
        dt_txt = item.get("dt_txt", "")
        
        # Extract hour from dt_txt
        hour = 12  # Default to midday
        if " " in dt_txt:
            time_part = dt_txt.split(" ")[1]
            if ":" in time_part:
                hour = int(time_part.split(":")[0])
        
        # Base UV by time of day (simplified)
        if 6 <= hour <= 8:
            base_uv = 2
        elif 9 <= hour <= 11:
            base_uv = 5
        elif 12 <= hour <= 14:
            base_uv = 8
        elif 15 <= hour <= 17:
            base_uv = 5
        elif 18 <= hour <= 20:
            base_uv = 2
        else:
            base_uv = 0
        
        # Reduce UV for cloudy/rainy weather
        if "cloud" in weather:
            base_uv = max(1, base_uv - 3)
        elif "rain" in weather or "thunderstorm" in weather:
            base_uv = max(0, base_uv - 5)
        elif "snow" in weather:
            base_uv = max(1, base_uv - 2)  # Snow reflects UV
        
        return base_uv

    def _calculate_activity_scores(self, daily_forecasts: List[Dict], avg_temp: Optional[float]) -> Dict[str, int]:
        """
        Calculate activity scores (0-100) based on weather conditions
        
        Returns:
            Dict with scores for beach, hiking, dog_walk, cycling
        """
        if not daily_forecasts or not avg_temp:
            return {"beach": 0, "hiking": 0, "dog_walk": 0, "cycling": 0}
        
        scores = {}
        
        # Calculate average conditions
        avg_rain_prob = sum(f["rain_probability"] for f in daily_forecasts) / len(daily_forecasts)
        avg_wind = sum(f["wind_speed"] for f in daily_forecasts) / len(daily_forecasts)
        max_rain_prob = max(f["rain_probability"] for f in daily_forecasts)
        
        # Beach score: warm, sunny, low wind, low rain
        beach_score = 0
        temp = float(avg_temp)
        if temp >= 20 and temp <= 30:
            beach_score += 50
        elif temp >= 15 and temp < 20:
            beach_score += 25
        elif temp > 30:
            beach_score += 30  # Too hot
        
        # Check for sunny/cloudy conditions
        sunny_days = sum(1 for f in daily_forecasts if "Clear" in f.get("weather", ""))
        beach_score += (sunny_days / len(daily_forecasts)) * 30
        
        if avg_wind < 20:
            beach_score += 20
        elif avg_wind < 35:
            beach_score += 10
        
        if avg_rain_prob < 20:
            beach_score += 10
        
        scores["beach"] = min(100, int(beach_score))
        
        # Hiking score: moderate temp, not too rainy, not too hot
        hiking_score = 0
        if temp >= 10 and temp <= 22:
            hiking_score += 50
        elif temp >= 5 and temp < 10:
            hiking_score += 30
        elif temp > 22 and temp <= 28:
            hiking_score += 25
        
        if max_rain_prob < 30:
            hiking_score += 30
        elif max_rain_prob < 50:
            hiking_score += 15
        
        if avg_wind < 30:
            hiking_score += 20
        
        scores["hiking"] = min(100, int(hiking_score))
        
        # Dog walk score: comfortable temp, any weather OK
        dog_walk_score = 50  # Base score
        
        if temp >= 5 and temp <= 25:
            dog_walk_score += 30
        elif temp >= 0 and temp < 5:
            dog_walk_score += 15
        elif temp > 25 and temp <= 30:
            dog_walk_score += 15  # Warm but OK
        elif temp > 30:
            dog_walk_score -= 10  # Too hot for dog
        elif temp < 0:
            dog_walk_score -= 10  # Too cold
        
        # Rain is OK for dog walks
        if avg_rain_prob < 50:
            dog_walk_score += 20
        
        scores["dog_walk"] = max(0, min(100, int(dog_walk_score)))
        
        # Cycling score: dry, moderate temp, not too windy
        cycling_score = 0
        if temp >= 12 and temp <= 25:
            cycling_score += 40
        elif temp >= 8 and temp < 12:
            cycling_score += 25
        elif temp > 25 and temp <= 30:
            cycling_score += 20
        
        if avg_rain_prob < 30:
            cycling_score += 35
        elif avg_rain_prob < 50:
            cycling_score += 15
        
        if avg_wind < 20:
            cycling_score += 25
        elif avg_wind < 35:
            cycling_score += 10
        else:
            cycling_score -= 15  # Too windy
        
        scores["cycling"] = max(0, min(100, int(cycling_score)))
        
        return scores

    def _check_weather_alert(self, daily_forecasts: List[Dict]) -> Optional[Dict]:
        """
        Check for adverse weather conditions that might affect travel
        
        Returns:
            Dict with alert info or None if no alerts
        """
        if not daily_forecasts:
            return None
        
        alerts = []
        
        # Check for heavy rain
        heavy_rain_days = [f for f in daily_forecasts if f.get("rain_probability", 0) >= 70]
        if heavy_rain_days:
            dates = [f["date"] for f in heavy_rain_days]
            alerts.append({
                "type": "heavy_rain",
                "severity": "warning",
                "message": f"Heavy rain expected on {', '.join(dates[-2:])}",
                "affected_dates": dates
            })
        
        # Check for extreme heat
        hot_days = [f for f in daily_forecasts if f.get("temp_max", 0) > 32]
        if hot_days:
            dates = [f["date"] for f in hot_days]
            alerts.append({
                "type": "extreme_heat",
                "severity": "warning",
                "message": f"High temperatures expected ({max(f['temp_max'] for f in hot_days)}°C)",
                "affected_dates": dates
            })
        
        # Check for extreme cold
        cold_days = [f for f in daily_forecasts if f.get("temp_min", 0) < 0]
        if cold_days:
            dates = [f["date"] for f in cold_days]
            alerts.append({
                "type": "extreme_cold",
                "severity": "info",
                "message": f"Below freezing temperatures expected",
                "affected_dates": dates
            })
        
        # Check for high wind
        windy_days = [f for f in daily_forecasts if f.get("wind_speed", 0) > 50]
        if windy_days:
            dates = [f["date"] for f in windy_days]
            alerts.append({
                "type": "high_wind",
                "severity": "warning",
                "message": f"Strong winds expected (up to {max(f['wind_speed'] for f in windy_days)} km/h)",
                "affected_dates": dates
            })
        
        # Check for thunderstorms
        storm_days = [f for f in daily_forecasts if "Thunderstorm" in f.get("weather", "")]
        if storm_days:
            dates = [f["date"] for f in storm_days]
            alerts.append({
                "type": "thunderstorm",
                "severity": "severe",
                "message": f"Thunderstorms expected - consider rescheduling",
                "affected_dates": dates
            })
        
        if alerts:
            # Return the most severe alert
            severity_order = {"severe": 3, "warning": 2, "info": 1}
            most_severe = max(alerts, key=lambda a: severity_order.get(a["severity"], 0))
            return most_severe
        
        return None

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
