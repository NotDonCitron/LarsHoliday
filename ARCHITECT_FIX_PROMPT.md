# Claude Opus Prompt: AirBnB Scraper Fix Architecture

```
You are an expert software architect specializing in web scraping, anti-bot evasion, and distributed systems. Your task is to architect a comprehensive plan to fix the critical limitations in an AirBnB vacation deal finder application.

## Project Context

The application is a Python-based vacation rental search tool that:
1. Scrapes Airbnb and Booking.com for vacation deals
2. Ranks deals by value (price, rating, reviews, pet-friendliness)
3. Integrates with weather API for recommendations
4. Provides a GUI interface for users

Current architecture:
- `holland_agent.py` - Main orchestrator
- `airbnb_scraper_enhanced.py` - Airbnb scraper (curl-cffi + Patchright fallback)
- `booking_scraper.py` - Booking.com scraper
- `rate_limit_bypass.py` - Rate limiting, caching, price alerts
- `deal_ranker.py` - Deal ranking algorithm

## Current Critical Limitations

### 1. Airbnb Scraping Reliability (~70% failure rate)
- curl-cffi requests frequently return HTTP 429 (rate limited)
- Patchright browser automation is slow (~45s) but more reliable
- Current fallback strategy: curl-cffi → Patchright → static data
- Problem: Users get static fallback data too often

### 2. Missing Data in Results
- Scraped data often lacks: pricing, ratings, review counts
- Need more reliable extraction of dynamic content
- JSON payloads sometimes incomplete or encrypted

### 3. No Real Alternative Data Sources
- Current: Only Airbnb + Booking.com
- Desired: Trip.com, Vrbo, Expedia, Hotels.com, local APIs
- No way to compare across platforms reliably

### 4. Performance Issues
- Patchright is too slow for interactive use
- No parallel scraping across sources
- No intelligent caching strategy

### 5. No Proactive Monitoring
- No automated scraping health checks
- No alerts when scraping fails repeatedly
- No adaptive behavior based on success rates

## Current Implementation Details

### Rate Limit Bypass (rate_limit_bypass.py)
```python
class RequestDelayer:
    min_delay: 3 seconds
    max_delay: 8 seconds

class ExponentialBackoff:
    base_delay: 20 seconds
    max_retries: 3
```

### SmartAirbnbScraper Strategy
1. Try curl-cffi (fast, ~2 seconds, ~30% success)
2. If 429 or empty results → Patchright (~45 seconds, ~80% success)
3. Static fallback (instant, 100% success, but low quality)

## Your Task

Create a comprehensive architectural plan to:

### Phase 1: Immediate Reliability Improvements
- [ ] Reduce 429 errors from 70% to <10%
- [ ] Improve Patchright speed (currently ~45s)
- [ ] Better handling of missing/extracted data

### Phase 2: Alternative Data Sources
- [ ] Integrate Trip.com API or scraping
- [ ] Add Vrbo scraping
- [ ] Add Hotels.com integration
- [ ] Implement cross-platform price comparison

### Phase 3: Performance Optimization
- [ ] Parallel scraping across sources
- [ ] Intelligent caching (per region/dates)
- [ ] Predictive pre-loading

### Phase 4: Monitoring & Self-Healing
- [ ] Health check endpoints
- [ ] Success rate tracking per strategy
- [ ] Automatic strategy rotation
- [ ] Alerting on persistent failures

## Requirements

1. **Must use ONLY free/open-source tools** - No paid APIs or services
2. **Must work on Linux (Ubuntu)** - Primary deployment target
3. **Must avoid legal issues** - Only scrape publicly available data, respect robots.txt
4. **Must be maintainable** - Clean code, good documentation
5. **Must be robust** - Graceful degradation when any source fails

## Deliverables

Provide a detailed architectural document with:

1. **Problem Analysis** - Root cause analysis of current failures
2. **Solution Architecture** - High-level design for each phase
3. **Implementation Plan** - Step-by-step coding tasks
4. **Risk Assessment** - What could go wrong, mitigation strategies
5. **Estimated Timeline** - Realistic effort for each phase
6. **Code Examples** - Key implementation patterns

Focus on practical, implementable solutions with actual code patterns that have been proven to work against Airbnb's anti-bot measures.
```
