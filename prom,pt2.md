

Integration in Agent:

python
# holland_agent.py - WEATHER INTEGRATION

import httpx
from datetime import datetime

class HollandVacationAgent:
    
    async def get_weather_forecast(self, city: str) -> Dict:
        """
        Integriere Wetter in Deal-Ranking
        """
        
        url = "https://api.openweathermap.org/data/2.5/forecast"
        
        params = {
            "q": city,  # Stadt name
            "appid": self.openweather_key,  # ← Dein API Key
            "units": "metric",  # Celsius
            "lang": "de"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            weather_data = response.json()
        
        return {
            "city": city,
            "forecast": weather_data.get("list", [])[:8],  # 5 Tage
            "avg_temp": self._calculate_avg_temp(weather_data)
        }
    
    def _calculate_avg_temp(self, data: Dict) -> float:
        """Durchschnittstemperatur berechnen"""
        temps = [item["main"]["temp"] for item in data.get("list", [])]
        return sum(temps) / len(temps) if temps else None
    
    async def enrich_deals_with_weather(self, 
                                        deals: List[Dict], 
                                        cities: List[str]):
        """
        Erweitere Deal-Ranking mit Wetter
        """
        
        for deal in deals:
            city = deal.get("location", "").split(",")[0]
            weather = await self.get_weather_forecast(city)
            
            # Wetter-Bonus zum Score
            if weather["avg_temp"] > 15:  # Schönes Wetter
                deal["weather_bonus"] = 1.2
            
            deal["weather_forecast"] = weather
        
        return deals

Beispiel API Response:

json
{
  "city": {
    "name": "Amsterdam",
    "country": "NL"
  },
  "list": [
    {
      "dt": 1706088000,
      "main": {
        "temp": 8.5,
        "feels_like": 6.2,
        "humidity": 75
      },
      "weather": [
        {
          "main": "Clouds",
          "description": "wolkig"
        }
      ]
    }
  ]
}

API Call Limits (Wichtig!) ⚠️
API	Free Limit	Empfehlung
Booking.com	100 calls/min	✅ Für Agent perfekt
OpenWeather	60 calls/min	✅ Cachen nach 10 min

Best Practice:

python
import asyncio
from functools import lru_cache
from datetime import datetime, timedelta

class APICache:
    def __init__(self, ttl_minutes: int = 10):
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache = {}
    
    def get(self, key: str):
        """Hole gecachte Daten"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return data
        return None
    
    def set(self, key: str, value):
        """Speichere mit Timestamp"""
        self.cache[key] = (value, datetime.now())

# Nutze es:
weather_cache = APICache(ttl_minutes=10)

async def get_weather(city):
    cached = weather_cache.get(f"weather_{city}")
    if cached:
        return cached  # 🚀 Instant
    
    result = await api_call(city)
    weather_cache.set(f"weather_{city}", result)
    return result

Vollständiger Setup für Claude Terminal 🚀

bash
# 1. Projekt erstellen
mkdir holland-agent
cd holland-agent

# 2. Python Umgebung
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate (Windows)

# 3. Dependencies
pip install -r requirements.txt

# 4. .env Datei erstellen
cat > .env << EOF
BOOKING_API_KEY="sk_live_your_key_here"
BOOKING_AFFILIATE_ID="956509"
OPENWEATHER_API_KEY="b1b15e88fa797225412429c1c50c122a1"
FIRECRAWL_API_KEY="fc-xxxxx"  # Optional
EOF

# 5. Agent starten
python holland_agent.py

requirements.txt:

text
httpx==0.25.0
python-dotenv==1.0.0
beautifulsoup4==4.12.0
asyncio==3.4.3

Häufige Fehler & Fixes 🔧
Error	Ursache	Fix
403 Forbidden	Falscher Affiliate ID	Check .env Datei
401 Unauthorized	API Key ungültig	Regeneriere auf Dashboard
429 Too Many Requests	Rate Limit überschritten	Cache + Warte 10 min
Connection Timeout	Server überlastet	Retry mit exponential backoff

Retry-Strategie:

python
async def call_with_retry(url: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=15.0)
                return response
        except Exception as e:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            print(f"Retry {attempt+1} in {wait_time}s...")
            await asyncio.sleep(wait_time)
    
    return None

Welcher OpenWeather Plan? 🌤️

Für deinen Agent: FREE Plan reicht komplett!

text
Free Plan:
✅ 1,000 calls/day
✅ 60 calls/min
✅ Current + Forecast Weather
✅ Für Hobby-Projekte perfekt
❌ Kein Historical Data
❌ Kein Priority Support

Professional:
💰 €30-300/Monat
✅ Unlimited Calls
✅ Historical Data
✅ Priority Support

Bereit zum Starten? Gib mir Bescheid wenn du:

    ✅ Booking Affiliate ID hast

    ✅ OpenWeather API Key hast

    ✅ .env konfiguriert hast

Dann können wir den kompletten Agent testen und in deinen Claude Terminal integrieren! 🎯

