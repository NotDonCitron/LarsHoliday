# Implementation Roadmap: Stability, Observability, Alerts, UX

## Goal
Implement the agreed improvement bundle end-to-end with measurable KPIs:

- Better stability and transparency during scraping
- Strict validation before ranking
- Robust price alerts without spam
- Optional periodic background searches
- Better dashboard filtering and feedback states
- Basic currency normalization foundation

---

## Phase 1 — Observability + KPI baseline

### Scope
- Introduce a lightweight run tracker with `run_id`, counters, and structured events.
- Add per-run KPI counters in search orchestration.
- Expose observability snapshot in API health endpoint.
- Record scraper strategy attempts (success/failure/duration/result_count).

### Files
- `observability.py` (new)
- `holland_agent.py`
- `api.py`
- `booking_scraper.py`
- `patchright_airbnb_scraper.py`

### Success Criteria
- Every search run has a `run_id`.
- API `/health` includes recent run summary.
- Strategy metrics in `scraper_metrics.json` are populated over time.

---

## Phase 2 — Validation + ranking normalization

### Scope
- Central deal validation before ranking:
  - required fields (`name`, `location`, `price_per_night`, `url`, `source`)
  - strict numeric checks (price > 0, rating bounds, reviews >= 0)
  - pet filter enforcement if requested
- Keep invalid deals with reason stats for diagnostics.
- Add basic currency normalization (EUR base) in ranking.

### Files
- `holland_agent.py`
- `deal_ranker.py`

### Success Criteria
- Invalid deals are excluded with reason counters.
- Ranker can normalize known currencies (`EUR`, `USD`, `GBP`) into EUR.

---

## Phase 3 — Price alerts hardening

### Scope
- Add cooldown-based dedupe for repeated alerts.
- Add per-property threshold overrides.
- Keep alert metadata to avoid duplicate spam.

### Files
- `rate_limit_bypass.py`
- `holland_agent.py` (pass threshold/cooldown config hooks)

### Success Criteria
- Repeated identical drops in short window do not trigger duplicate alerts.
- Alerts still trigger for meaningful new drops.

---

## Phase 4 — Scheduler (CLI)

### Scope
- Add CLI scheduling mode:
  - run search periodically every N minutes
  - optional fixed number of runs
- Keep one-shot behavior as default.

### Files
- `main.py`

### Success Criteria
- `main.py` can execute periodic runs without external cron.

---

## Phase 5 — Dashboard UX upgrades

### Scope
- Add client-side filters:
  - max nightly price
  - minimum rating
  - pet-friendly-only toggle
- Add clear filter action and live result status text.
- Improve error/empty communication and add price trend badge when available.

### Files
- `frontend_dashboard.html`

### Success Criteria
- Users can narrow results without new API call.
- Filtered counts are visible and states are understandable.

---

## Phase 6 — Test & docs

### Scope
- Update/add tests for validation, cache behavior, alert dedupe/cooldown, and scheduler flow.
- Document changes and operations guide.

### Files
- `tests/test_agent_validation.py`
- `tests/test_price_alerts.py`
- `tests/test_caching.py`
- `DOCUMENTATION.md`

### Success Criteria
- Core new behavior covered by tests.
- Operational usage documented.

---

## Dependencies and Order
1. Phase 1 (foundation)
2. Phase 2 (data quality + ranking)
3. Phase 3 (alerts)
4. Phase 4 (scheduler)
5. Phase 5 (UX)
6. Phase 6 (tests/docs)

---

## KPI Targets
- 429 incident rate trend visible in health metrics
- Cache hit rate tracked per run
- Validation rejection reasons available for troubleshooting
- Price alert duplicates reduced via cooldown/dedupe
- Dashboard usability improved via local filtering and clearer states
