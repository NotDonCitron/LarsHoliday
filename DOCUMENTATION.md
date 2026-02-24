# Lars Urlaubs-Deals: Technical Documentation

## Overview
This project is an AI-powered vacation deal finder specializing in finding dog-friendly accommodations across multiple platforms (Airbnb, Booking.com). It is designed to be resilient against bot detection and rate limits while providing high-quality, ranked results.

## Core Features

### 1. Smart Scrapers (Multi-Strategy)
Both Airbnb and Booking.com scrapers follow a tiered strategy to ensure results even under high pressure:
- **Strategy 1: Local Curl (Fast/Free):** Uses `httpx` with rotated User-Agents to attempt a direct request.
- **Strategy 2: Firecrawl Cloud (Reliable):** Delegated scraping via Firecrawl API, which handles headless browser rendering, scrolling, and proxy rotation.
- **Strategy 3: Static Fallback (Always Works):** If all else fails, the system returns predefined high-quality example data to ensure the UI remains functional.

### 2. Rate Limit Bypass
- **User-Agent Rotation:** A pool of modern browser strings is used to mimic different users.
- **Adaptive Delays:** Requests are staggered with random delays (5-15s). The delay automatically increases if 429 (Rate Limit) errors are detected.
- **Exponential Backoff:** Retries include increasing wait times to respect server limits.

### 3. Price Alert System
- **Persistence:** All found properties are hashed and stored in `price_alerts.json`.
- **Logic:** If a property is found again with a price drop of **>20%**, an alert is triggered.
- **UI Integration:** Active alerts are prominently displayed in the Web Dashboard and logged in the Desktop GUI.

### 4. Intelligent Caching
- **Mechanism:** Search results are cached locally in `.search_cache.json` with a 30-minute Time-To-Live (TTL).
- **Efficiency:** Repeated searches for the same city and dates are served instantly, saving API credits and reducing server load.

### 5. Booking.com Reliability Fix
- **Targeted Parsing:** The parser specifically looks for `data-testid="price-and-discounted-price"` elements.
- **Fallback Parsing:** If HTML parsing fails due to obfuscated classes, the system automatically falls back to parsing the **Markdown** version of the page provided by Firecrawl.
- **Price Intelligence:** The system distinguishes between nightly rates and total stay costs based on the search context and budget.

## Tech Stack
- **Backend:** Python 3.14+, FastAPI, Uvicorn.
- **Scraping:** httpx, BeautifulSoup4, Firecrawl API.
- **Frontend:** Responsive HTML/JS Dashboard with Tailwind CSS and Material Design principles.
- **Persistence:** Local JSON files for caching and alerts.

## Testing
Comprehensive TDD suite in the `tests/` directory:
- `test_smart_scraper.py`: Fallback logic verification.
- `test_booking_smart.py`: Booking-specific scraper tests.
- `test_price_alerts.py`: Alert system verification.
- `test_caching.py`: Cache hit/miss verification.

## Deployment
- **GitHub:** Main source repository ([NotDonCitron/LarsHoliday](https://github.com/NotDonCitron/LarsHoliday)).
- **Hugging Face Spaces:** Live web deployment ([PHhTTPS/LarsHoliday](https://huggingface.co/spaces/PHhTTPS/LarsHoliday)).
