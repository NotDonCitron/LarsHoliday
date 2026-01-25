# Project Knowledge (CLAUDE.md)

## Project Overview
Holland Vacation Deal Finder - AI-powered vacation deal finder for Netherlands. Searches multiple sources (Booking.com, Airbnb, Center Parcs) for budget-friendly, dog-friendly accommodations for families.

## Tech Stack
- **Language**: Python 3.8+
- **Main Dependencies**:
  - httpx (async HTTP client)
  - python-dotenv (environment variables)
  - beautifulsoup4 (HTML parsing)
- **External Tools**: agent-browser CLI (browser automation)
- **APIs**: OpenWeather API (weather forecasts)

## Important Files
- `main.py` - CLI entry point with argument parsing
- `holland_agent.py` - Main orchestrator that coordinates all searches
- `booking_scraper.py` - Booking.com scraper using agent-browser
- `airbnb_scraper.py` - Airbnb scraper using agent-browser
- `weather_integration.py` - OpenWeather API integration with caching
- `deal_ranker.py` - Multi-factor scoring algorithm for ranking deals
- `requirements.txt` - Python dependencies
- `.env` - API keys and configuration (not in git)

## How It Works
1. User provides cities, dates, and group size via CLI
2. Agent searches all sources in parallel for each city
3. Weather data is fetched and cached (10-min TTL)
4. Deals are scored using multi-factor algorithm:
   - Price score (0-40 points)
   - Rating score (0-30 points)
   - Review count (0-20 points)
   - Dog-friendly multiplier (1.4x)
   - Weather bonus (1.2x if temp > 15°C)
5. Top 10 deals are returned with recommendations

## Usage
```bash
# Installation
pip install -r requirements.txt

# Basic search
python main.py --cities Amsterdam --checkin 2026-02-15 --checkout 2026-02-22

# Multi-city with budget
python main.py --cities "Amsterdam,Rotterdam,Zandvoort" --checkin 2026-02-15 --checkout 2026-02-22 --budget-max 200

# Human-readable output
python main.py --cities Amsterdam --checkin 2026-02-15 --checkout 2026-02-22 --output summary
```

## Configuration
Environment variables in `.env`:
- `OPENWEATHER_API_KEY` - OpenWeather API key (required)
- `FIRECRAWL_API_KEY` - Firecrawl API key (optional)
- `AGENT_BROWSER_PATH` - Path to agent-browser executable
- `AGENT_BROWSER_SESSION` - Browser session name

## Architecture
- **Async/parallel**: All city searches run concurrently
- **Caching**: Weather API responses cached for 10 minutes
- **Fallback data**: Static Center Parcs data + fallback for scrapers
- **Browser automation**: agent-browser CLI for JavaScript-heavy sites

## Known Issues / TODOs
- [ ] agent-browser integration needs real testing (currently uses fallback data)
- [ ] Add retry logic for failed API calls
- [ ] Implement actual HTML parsing for Booking.com/Airbnb snapshots
- [ ] Add more vacation sources (Hotels.com, Vrbo)
- [ ] Add Telegram notifications for deal alerts
- [ ] Implement price tracking over time

## Notes
- Free tier limits: OpenWeather (60 calls/min, 1000/day)
- agent-browser requires Node.js and npm installation
- Center Parcs data is static and dog-friendly by default
- Weather bonus only applies if avg temp > 15°C
- All prices in EUR
