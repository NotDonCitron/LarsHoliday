# Lars Urlaubs-Deals: Technical Documentation

## Overview
This project is an AI-powered vacation deal finder specializing in dog-friendly accommodations across multiple platforms (Airbnb, Booking.com).

It is designed for:
- resilient scraping under rate limiting,
- unified scoring and filtering,
- transparent run diagnostics via observability and health data,
- practical dashboard usability for day-to-day deal checks.

## Recent Improvements (2026-02)
The latest enhancement cycle added:
- **Run-level observability** with run IDs, KPI counters, and structured events.
- **Central deal validation** before ranking.
- **Robust price alerts** (dedupe, cooldown, per-deal threshold overrides).
- **CLI scheduler mode** for periodic background searches.
- **Dashboard UX upgrades** (client-side filters, better empty/error states, price trend chips).
- **Currency normalization to EUR** for fair cross-market ranking.

## Core Features

### 1. Smart Scrapers (Multi-Strategy)
Both Airbnb and Booking.com scrapers follow a tiered strategy:
- **Strategy 1: Local Curl/HTTP** (fastest, cheapest)
- **Strategy 2: Firecrawl Cloud** (reliable rendered fallback)
- **Strategy 3: Static fallback data** (keeps UI functional if everything else fails)

Strategy attempts are instrumented with source/strategy duration and success metrics.

### 2. Rate Limit Bypass
- **User-Agent rotation**
- **Adaptive delays** that increase under pressure
- **Exponential backoff** for repeated throttling
- **Optional session warming** for more realistic request patterns

### 3. Central Validation Pipeline
All raw deals are validated before ranking:
- required fields (name, location, source, url)
- numeric sanity checks (price/rating/reviews)
- budget boundaries
- pet-friendly enforcement when pets are requested

Validation output is returned in API/agent results (`valid_count`, `rejected_count`, reasons).

### 4. Observability & KPI Tracking
A lightweight observability layer tracks each search run:
- unique run ID
- lifecycle events (`run_started`, source cache hits/misses, errors, run_finished)
- per-run counters (cache hits, misses, valid deals, triggered alerts, etc.)
- run summaries retained for health diagnostics

`/health` includes an observability snapshot with active/recent runs.

### 5. Price Alert System
Price alerts are persisted and now include robustness controls:
- configurable drop threshold (global + per-deal override)
- dedupe window for repeated identical updates
- cooldown window to suppress duplicate alerts at same price
- capped history size per property

### 6. Intelligent Caching
- Local JSON cache (`.search_cache.json`) with TTL
- repeated searches with same parameters return quickly
- cache metrics included in observability

### 7. Deal Ranking and Currency Normalization
Deals are scored by price/rating/reviews with pet/weather multipliers.

All ranking prices are normalized to **EUR** using built-in FX rates (or optional custom per-deal `fx_rate_to_eur`), while preserving original currency/price in output metadata.

### 8. Dashboard UX
The web dashboard includes:
- source tabs and sorting modes,
- client-side filters (minimum rating, max EUR/night, pet-only),
- explicit empty-state messaging ("no source results" vs "filtered out"),
- improved fetch error handling,
- price trend badges when previous price context is available.

## Scheduler Mode (CLI)
You can run periodic searches from CLI:

```bash
python main.py \
  --cities "Amsterdam,Rotterdam" \
  --checkin 2026-03-01 \
  --checkout 2026-03-05 \
  --schedule-minutes 30 \
  --max-runs 6
```

- `--schedule-minutes 0` keeps one-shot behavior (default).
- `--max-runs 0` means unlimited scheduled cycles.

## Tech Stack
- **Backend:** Python, FastAPI, Uvicorn
- **Scraping:** httpx, BeautifulSoup4, Firecrawl API
- **Frontend:** Responsive HTML/JS dashboard (Tailwind-style utility classes)
- **Persistence:** Local JSON files for cache and alerts

## Testing
Primary regression coverage for the new features includes:
- `tests/test_price_alerts.py` (dedupe/cooldown/override + agent integration)
- `tests/test_agent_validation.py` (pet filter + validation counters)
- `tests/test_currency_normalization.py` (EUR normalization + custom FX override)
- `tests/test_scheduler_cli.py` (scheduler CLI argument parsing)
- `tests/test_caching.py` (cache behavior still valid)

Example run:

```bash
PYTHONPATH=. pytest -q \
  tests/test_price_alerts.py \
  tests/test_agent_validation.py \
  tests/test_currency_normalization.py \
  tests/test_scheduler_cli.py
```

## Deployment Notes
- Local web mode: `uvicorn api:app --reload`
- Health check endpoint: `/health`
- Search endpoint: `/search`

## Repository / Distribution
- Main source repository and deployment references remain unchanged.
