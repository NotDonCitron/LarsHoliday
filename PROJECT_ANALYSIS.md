# Project Analysis Documentation

## Holland Vacation Deal Finder

### Project Overview

**AI-powered vacation deal finder** that searches across multiple booking platforms to find budget-friendly, dog-friendly accommodations primarily for the Netherlands, with international expansion capabilities.

---

## Similar Projects & Competitor Analysis

### Directly Referenced Projects

| Project | URL | Purpose | Relevance |
|---------|-----|---------|----------|
| Vercel Agent Browser | https://github.com/vercel-labs/agent- | Browser automation CLI | Used for complex scraping tasks |
| Firecrawl | https://app.firecrawl.dev/ | Server-side scraping with LLM extraction | Alternative to curl-cffi for JavaScript-heavy sites |
| Booking.com Affiliate API | https://developers.booking.com | Official API for property search | Potential replacement for scraping |

### Technology Stack References

The codebase references these technologies as alternatives or enhancements:

1. **Firecrawl-py** - LLM-based extraction from scraped pages
   - Pros: Handles JavaScript rendering, structured extraction
   - Cons: Requires API key, usage limits
   - Integration: Would replace curl-cffi for complex sites

2. **SeleniumBase** - Browser automation framework
   - Referenced in prompt.md as alternative to Firecrawl
   - Pros: Full browser control, intercept network requests
   - Cons: Heavy resource usage, slower

3. **Booking.com Affiliate API**
   - Official API access to live pricing
   - Pros: Reliable, no scraping, direct booking integration
   - Cons: Requires affiliate registration

### Similar Open Source Projects (Search Keywords)

Based on the project scope, here are search terms to find similar projects on GitHub:

| Search Keywords | Expected Results |
|----------------|-----------------|
| `airbnb scraper python` | Various Airbnb listing extractors |
| `booking.com scraper` | Hotel/booking site scrapers |
| `vacation deal finder` | Travel aggregators, price comparison tools |
| `hotel price comparison` | Multi-source hotel search tools |
| `travel deal aggregator` | Cross-platform deal finders |
| `pet-friendly travel` | Niche pet-friendly booking tools |

### Common Patterns in Similar Projects

1. **Multi-source Aggregation**
   - Expedia, Hotels.com, Booking.com, Airbnb
   - API-first vs scraping approaches

2. **Browser Automation**
   - Playwright, Puppeteer, Selenium
   - curl-cffi for lightweight stealth

3. **Deal Ranking Algorithms**
   - Price normalization (per night vs total)
   - Review weighting
   - Location-based scoring

4. **Weather Integration**
   - OpenWeather API (common choice)
   - Weather-based recommendations

### Potential Enhancements Based on Competitor Research

1. **Add Expedia/Hotels.com support** - Common additional sources
2. **Implement Firecrawl fallback** - For sites blocking curl-cffi
3. **Consider Booking.com Affiliate API** - More reliable than scraping
4. **Add price history tracking** - Common in deal finder apps
5. **Implement alerts/notifications** - Price drop alerts

---

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     VacationApp (gui_app.py)                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   Tkinter Dark Mode GUI                     │ │
│  │  • Search form (cities, dates, budget, pets)              │ │
│  │  • Results display (scrollable cards)                     │ │
│  │  • Favorites sidebar (persisted to favorites.json)        │ │
│  │  • Activity log (stdout redirect)                        │ │
│  │  • Report generation (HTML, PDF)                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   VacationAgent (holland_agent.py)              │
│  Orchestrates multi-source search, validation, and ranking     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │ BookingScraper  │  │ AirbnbScraper   │  │   Weather     │  │
│  │   (curl-cffi)   │  │   (curl-cffi)  │  │ Integration   │  │
│  └────────┬────────┘  └────────┬────────┘  └───────┬───────┘  │
│           │                    │                     │          │
│           └────────────────────┼─────────────────────┘          │
│                                ▼                                │
│                    DealRanker (deal_ranker.py)                  │
│                    Multi-factor scoring algorithm               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Sources                               │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Booking.com  │  │   Airbnb     │  │   Center Parcs      │  │
│  │  (scraper)   │  │   (scraper)  │  │   (static data)     │  │
│  └──────────────┘  └──────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Details

### 1. Entry Points

| File | Purpose | Usage |
|------|---------|-------|
| [`main.py`](main.py) | CLI entry point | `python main.py --cities Amsterdam --checkin 2026-02-15 --checkout 2026-02-22` |
| [`gui_app.py`](gui_app.py) | Tkinter desktop app | `python gui_app.py` |
| [`holland_agent.py`](holland_agent.py) | Direct agent usage | `python holland_agent.py` |

### 2. Scraper Modules

#### [`booking_scraper.py`](booking_scraper.py)
- **Purpose**: Scrapes Booking.com for pet-friendly accommodations
- **Stealth**: Uses `curl-cffi` with Chrome 120 impersonation
- **Filters**: Pet-friendly (`ht_id=220`), vacation homes
- **Fallback**: Static data for Amsterdam, Rotterdam, Zandvoort
- **Key Methods**:
  - `search_booking(city, checkin, checkout, adults)` - Main search
  - `_parse_html(soup, city, nights)` - HTML parsing
  - `_get_fallback_data(city, checkin, checkout, adults)` - Fallback data

#### [`airbnb_scraper.py`](airbnb_scraper.py)
- **Purpose**: Scrapes Airbnb for pet-friendly homes
- **Stealth**: Uses `curl-cffi` with randomized browser impersonation (chrome120, chrome119, safari15_3, edge101)
- **Retry Logic**: 5 attempts with exponential backoff (2^n * 30s) for 429 errors
- **Parsing**: Extracts JSON from `niobeClientData` script tags
- **Fallback**: Static data for Amsterdam, Rotterdam, Zandvoort
- **Key Methods**:
  - `search_airbnb(region, checkin, checkout, adults)` - Main search
  - `_parse_html(soup, region, checkin, checkout, required_capacity)` - JSON parsing
  - `_get_fallback_data(region, checkin, checkout, adults)` - Fallback data

### 3. Core Logic Modules

#### [`deal_ranker.py`](deal_ranker.py)
**Multi-factor Scoring Algorithm**:

| Factor | Weight | Formula |
|--------|--------|---------|
| Price Score | 0-40 pts | `max(0, 40 - price/3)` |
| Rating Score | 0-30 pts | `rating * 6` |
| Review Count | 0-20 pts | `min(20, reviews/20)` |
| Dog-Friendly | 1.4x | Multiplier |
| Weather Bonus | 1.2x | If avg temp > 15°C |

**Recommendation Tiers**:
- 🔥 EXCELLENT: Score > 80
- ✅ VERY GOOD: Score > 60
- 👍 GOOD: Score > 40
- ⚠️ BUDGET: Score ≤ 40

#### [`weather_integration.py`](weather_integration.py)
- **API**: OpenWeather 5-day forecast (3-hour intervals)
- **Caching**: 10-minute TTL via `APICache`
- **Bonus**: 1.2x if average temperature > 15°C
- **Key Methods**:
  - `get_weather_forecast(city)` - Fetch forecast
  - `enrich_deals_with_weather(deals, cities)` - Add weather data

### 4. Persistence Modules

#### [`favorites_manager.py`](favorites_manager.py)
- **Storage**: `favorites.json` (JSON file)
- **Methods**:
  - `add_favorite(deal)` - Add with duplicate detection
  - `remove_favorite(deal_url)` - Remove by URL
  - `get_all()` - Retrieve all favorites

#### [`report_generator.py`](report_generator.py)
- **Output**: PDF reports via FPDF2
- **Features**: Search params, deal cards, clickable links
- **Character Handling**: Latin-1 encoding with emoji replacement

### 5. Supporting Files

| File | Purpose |
|------|---------|
| [`generate_full_html.py`](generate_full_html.py) | HTML report generation |
| [`test_suite.sh`](test_suite.sh) | Test runner script |
| [`requirements.txt`](requirements.txt) | Dependencies |

---

## Data Model

### Deal Structure
```python
{
    "name": str,                    # Property name
    "location": str,                 # City/region
    "price_per_night": float,        # EUR per night
    "total_cost_for_trip": float,    # Price * nights
    "rating": float,                # 0-5 stars
    "reviews": int,                  # Review count
    "pet_friendly": bool,           # Dog-friendly flag
    "source": str,                  # "booking.com", "airbnb", "center-parcs"
    "url": str,                    # Direct booking link
    "rank_score": float,            # Calculated score (0-100)
    "recommendation": str,          # Human-readable tier
    "weather_forecast": dict,       # Optional weather data
    "weather_bonus": float          # 1.0 or 1.2
}
```

### Search Parameters
```python
{
    "cities": List[str],            # e.g., ["Amsterdam", "Berlin"]
    "checkin": str,                 # YYYY-MM-DD
    "checkout": str,                # YYYY-MM-DD
    "nights": int,                  # Calculated difference
    "group_size": int,              # Number of adults
    "pets": int,                    # Number of dogs
    "budget_range": str             # e.g., "€40-€250"
}
```

---

## External Dependencies

### Python Packages
```
httpx==0.25.0              # Async HTTP client
python-dotenv==1.0.0        # Environment variables
beautifulsoup4==4.12.0      # HTML parsing
curl-cffi                   # Stealth HTTP requests
fpdf2==2.7.9               # PDF generation
```

### External APIs
| API | Purpose | Free Tier |
|-----|---------|-----------|
| OpenWeather | Weather forecasts | 60 calls/min, 1000/day |
| Firecrawl | Enhanced scraping | Optional |

### Browser Automation
- **agent-browser**: Node.js CLI tool for complex browser tasks (optional)

---

## Configuration

### Environment Variables (`.env`)
```bash
FIRECRAWL_API_KEY=your_firecrawl_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
AGENT_BROWSER_SESSION=holland-deals
AGENT_BROWSER_PATH=/path/to/agent-browser
```

---

## Usage Examples

### CLI Search
```bash
# Basic search
python main.py --cities Amsterdam --checkin 2026-02-15 --checkout 2026-02-22

# Multi-city with budget
python main.py --cities "Amsterdam,Rotterdam,Zandvoort" --checkin 2026-02-15 --checkout 2026-02-22 --budget-max 200

# Custom group and pets
python main.py --cities Amsterdam --checkin 2026-03-01 --checkout 2026-03-08 --adults 2 --pets 1

# Human-readable output
python main.py --cities Amsterdam --checkin 2026-02-15 --checkout 2026-02-22 --output summary --top 5
```

### GUI Application
```bash
python gui_app.py
# Opens Tkinter window with:
# - Search form (destinations, dates, budget, pets toggle)
# - Scrollable results cards
# - Favorites sidebar
# - Activity log
# - Export buttons (HTML, PDF)
```

---

## Project Structure

```
/home/phhttps/Downloads/AirBnB/
├── .claude/                      # Claude Code context
│   └── conductor/               # Project management
│       ├── index.md             # Context index
│       ├── product.md           # Product definition
│       ├── tech-stack.md        # Technology choices
│       ├── workflow.md          # Development workflow
│       ├── code_styleguides/    # Coding standards
│       └── tracks/              # Feature tracks
│           ├── data_portability/
│           ├── international_expansion/
│           └── persistence/
├── Core Application Files
│   ├── main.py                  # CLI entry point
│   ├── holland_agent.py         # Main orchestrator
│   ├── booking_scraper.py      # Booking.com scraper
│   ├── airbnb_scraper.py       # Airbnb scraper
│   ├── deal_ranker.py          # Scoring algorithm
│   ├── weather_integration.py   # Weather API
│   ├── gui_app.py              # Tkinter GUI
│   ├── favorites_manager.py    # Favorites persistence
│   └── report_generator.py     # PDF reports
├── Configuration
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example            # Environment template
│   ├── README.md               # Main documentation
│   └── QUICK-START.md          # Quick start guide
├── Tests
│   └── tests/                  # Test suite (22+ test files)
└── Output Files
    ├── last_search_report.html # Latest HTML report
    ├── favorites.json          # Saved favorites
    └── wochenende_empfehlungen.html  # German weekend recommendations
```

---

## Known Issues & Limitations

1. **Rate Limiting**: Airbnb scraper may hit 429 errors; uses exponential backoff
2. **Fallback Data**: When scraping fails, static fallback data is used
3. **Browser Detection**: Some sites may block automated requests
4. **Weather API**: Requires valid OpenWeather API key for weather bonuses
5. **Scraping Fragility**: HTML structure changes on target sites may break parsers

---

## Development Guidelines

### Code Style
- Follow [`conductor/code_styleguides/python.md`](conductor/code_styleguides/python.md)
- Type hints required for all functions
- Docstrings for public methods

### Testing
- Tests located in [`tests/`](tests/)
- Run with: `bash test_suite.sh`
- Target: >80% code coverage

### Workflow
- Follow [`conductor/workflow.md`](conductor/workflow.md)
- Tasks tracked in `plan.md`
- Phases marked with git checkpoint commits

---

## Key Features Summary

| Feature | Status | Location |
|---------|--------|----------|
| Multi-source search | ✅ | holland_agent.py |
| Pet-friendly filtering | ✅ | All scrapers |
| Weather integration | ✅ | weather_integration.py |
| Multi-factor scoring | ✅ | deal_ranker.py |
| Tkinter GUI | ✅ | gui_app.py |
| Dark mode UI | ✅ | gui_app.py |
| Favorites persistence | ✅ | favorites_manager.py |
| PDF export | ✅ | report_generator.py |
| HTML reports | ✅ | generate_full_html.py |
| International expansion | 🔄 | tracks/international_expansion/ |
| Data portability | 🔄 | tracks/data_portability/ |

---

## Recent Changes & Tracks

### Completed Tracks
- GUI Implementation (tkinter-based dark mode)
- Data Integrity (price normalization, capacity filtering)

### Active Tracks
- **International Expansion**: Adding Belgium, Germany support
- **Data Portability**: Export to PDF, Excel

### Future Enhancements
- Additional booking platforms (Expedia, local parks)
- Email notifications for price drops
- Mobile app (Flutter/React Native)
- User accounts with cloud sync

---

*Documentation generated for project analysis. Last updated: 2026-02-11*

---

## Airbnb Blocking Problem Analysis

### Problem Description

**Issue**: Airbnb blocks requests with 429 errors and provides incorrect links due to rate limiting and bot detection.

**Current Implementation**:
- Uses `curl-cffi` with randomized browser impersonation
- Implements 5-retry exponential backoff (2^n * 30s)
- Still encounters blocking and incorrect link generation

### Root Causes

1. **Detection Methods Airbnb Uses**:
   - `navigator.webdriver` flag detection
   - Runtime/Console API leaks
   - Command flag detection (`--enable-automation`)
   - Request pattern analysis (too many requests too fast)
   - Missing or inconsistent browser fingerprints

2. **Current Weaknesses**:
   - curl-cffi provides basic impersonation but lacks advanced fingerprint patching
   - No proxy rotation
   - No CAPTCHA handling
   - Limited retry strategies

### Solutions from GitHub Research

#### Option 1: Patchright (Recommended)

**Repository**: https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python

**Stars**: 1,118+ (Python), 2,302+ (NodeJS)

**What it does**:
- Undetectable Playwright fork with full browser fingerprint patching
- Patches `Runtime.enable` and `Console.enable` leaks
- Removes automation flags (`--enable-automation`, `--disable-blink-features=AutomationControlled`)
- Drop-in replacement for Playwright

**Pros**:
- Nearly undetectable
- Full JavaScript rendering
- Handles complex JavaScript-heavy sites
- Supports CAPTCHA solving with additional modules

**Cons**:
- Heavy (requires full browser installation)
- Slower than curl-cffi
- Resource intensive

**Installation**:
```bash
pip install patchright-python
```

**Usage Example**:
```python
import patchright

browser = patchright.chromium.launch()
page = browser.new_page()
page.goto('https://www.airbnb.com/s/amsterdam/homes')
content = page.content()
```

#### Option 2: Rebrowser Patches

**Repository**: https://github.com/rebrowser/rebrowser-patches

**Stars**: 1,233+

**What it does**:
- Collection of patches for Puppeteer and Playwright
- Avoids Cloudflare and DataDome CAPTCHA
- Can be enabled/disabled on demand

**Pros**:
- Modular (use only what you need)
- Works with existing Playwright/Puppeteer setups
- Community maintained

#### Option 3: Scrapling

**Repository**: https://github.com/D4Vinci/Scrapling

**Stars**: 8,961+

**What it does**:
- High-performance Python web scraping library
- Undetectable, flexible, powerful
- Anti-detection built-in

**Pros**:
- Lightweight compared to full browser
- High performance
- Good anti-detection

**Cons**:
- Less mature than Playwright-based solutions
- Limited JavaScript rendering

#### Option 4: Enhanced curl-cffi (Current + Improvements)

Improve existing curl-cffi approach:
```python
from curl_cffi import requests
import asyncio
import random
from typing import List

class EnhancedAirbnbScraper:
    def __init__(self):
        self.session = requests.Session()
        self.browsers = [
            "chrome120", "chrome119", "chrome118",
            "safari15_5", "safari16_0", "safari16_6",
            "edge120", "edge119", "edge118"
        ]
        self.proxy_list = self._load_proxies()  # Implement proxy rotation
    
    async def search_airbnb_improved(self, region, checkin, checkout, adults=4):
        await asyncio.sleep(random.uniform(5, 15))
        proxy = random.choice(self.proxy_list) if self.proxy_list else None
        impersonation = random.choice(self.browsers)
        
        response = self.session.get(
            url,
            impersonate=impersonation,
            proxy=proxy,
            timeout=30,
            allow_redirects=True
        )
```

#### Option 5: Firecrawl (API-based)

**Repository**: https://app.firecrawl.dev/

**What it does**:
- Server-side scraping with LLM extraction
- Handles JavaScript rendering
- Returns structured data

**Pros**:
- No blocking on your end
- Structured extraction
- CAPTCHA handling included

**Cons**:
- Requires API key
- Usage limits
- Cost per request

### Recommended Solution for Your Project

**For Airbnb specifically**, I recommend:

1. **Short-term**: Improve curl-cffi with:
   - Proxy rotation (residential proxies)
   - More sophisticated delays
   - User-Agent rotation

2. **Long-term**: Integrate Patchright:
   - Replace curl-cffi for Airbnb with Patchright
   - Keep curl-cffi for Booking.com (less aggressive blocking)
   - Use Patchright only when curl-cffi fails

### Proxy Providers for Rotation

| Provider | Type | Price Range |
|----------|------|-------------|
| Bright Data | Residential | $15-20/GB |
| SmartProxy | Residential | $12-15/GB |
| Oxylabs | Residential | $18-25/GB |
| Thordata | Residential | $10-15/GB |
| Hyperbrowser | Cloud Browsers | Pay-per-session |

### Implementation Plan (Hybrid Approach)

```python
import asyncio
from curl_cffi import requests
import patchright

class HybridAirbnbScraper:
    """Uses curl-cffi first, falls back to Patchright on 429"""
    
    def __init__(self):
        self.curl_session = requests.Session()
        self.patchright_browser = None
    
    async def search_airbnb(self, region, checkin, checkout, adults=4):
        try:
            return await self._search_with_curl(region, checkin, checkout, adults)
        except BlockingError:
            return await self._search_with_patchright(region, checkin, checkout, adults)
```

