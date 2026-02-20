# Implementation Plan - Live Data Integrity

## Phase 1: Scraper Audit & Repair
- [ ] Task: Eliminate Mocks in `holland_agent.py`
    - [ ] Remove `_parse_booking_html` fallback data.
    - [ ] Ensure `_search_center_parcs` uses real logic or a live scraper.
- [ ] Task: Fix Booking.com Deep Links
    - [ ] Update `booking_scraper.py` to extract the full URL including affiliate/tracking parameters for direct booking.
- [ ] Task: Verify Airbnb Patchright Scraper
    - [ ] Test `patchright_airbnb_scraper.py` against live Airbnb pages.
    - [ ] Ensure the "Redirect to Search" fallback actually works with the selected dates.

## Phase 2: Data Validation
- [ ] Task: Real-time Link Validation
    - [ ] Implement a small check to ensure generated links return a 200 OK status.
- [ ] Task: Image Extraction
    - [ ] Update scrapers to extract the actual thumbnail URL from the property cards (no more placeholder images).

## Phase 3: API & UI Sync
- [ ] Task: Update API Response
    - [ ] Ensure `api.py` passes the new real image URLs and direct links to the frontend.
- [ ] Task: Frontend Update
    - [ ] Update `frontend_dashboard.html` to use `${deal.image_url}` instead of Unsplash placeholders.
