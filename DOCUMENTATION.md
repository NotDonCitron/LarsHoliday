# Lars Urlaubs-Deals: Technical Documentation

## Overview
This project is an AI-powered vacation deal finder specializing in finding dog-friendly accommodations across multiple platforms (Airbnb, Booking.com).

## Core Features
- **Smart Scrapers:** Multi-strategy scraping (Local Curl -> Firecrawl Cloud -> Fallback).
- **Rate Limit Bypass:** Rotated User-Agents, adaptive delays, and exponential backoff to prevent blocks.
- **Price Alert System:** Monitors price history and alerts on drops >20%.
- **Intelligent Caching:** 30-minute persistent cache to speed up repeated searches.
- **Weather Integration:** Real-time forecasts for destination cities.

## Tech Stack
- **Backend:** Python 3.14+, FastAPI, Uvicorn.
- **Scraping:** httpx, BeautifulSoup4, Firecrawl API.
- **Frontend:** Responsive HTML/JS Dashboard with Tailwind CSS.
- **Persistence:** Local JSON files for caching and alerts.

## Testing
Comprehensive TDD suite in the `tests/` directory:
- `test_smart_scraper.py`: Fallback logic verification.
- `test_booking_smart.py`: Booking-specific scraper tests.
- `test_price_alerts.py`: Alert system verification.
- `test_caching.py`: Cache hit/miss verification.

## Deployment
- **GitHub:** Main source repository.
- **Hugging Face Spaces:** Live web deployment.
