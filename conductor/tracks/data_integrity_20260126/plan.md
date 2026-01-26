# Implementation Plan - Fix Data Integrity Issues

## Phase 1: Diagnosis and Validation
- [x] Task: Create a reproduction script to isolate scraper output a939af5
    - [ ] Create `debug_scrapers.py` to run `BookingScraper` and `AirbnbScraper` independently with verbose logging.
    - [ ] capture raw HTML/JSON responses for a few sample queries to inspect the actual DOM structure vs. expected selectors.
- [x] Task: Analyze Booking.com price discrepancies 1a122b4
    - [ ] Run `debug_scrapers.py` for Booking.com.
    - [ ] Compare scraped prices against the actual website values for specific properties.
    - [ ] Identify if the issue is "price per night" vs "total price" or currency parsing.
- [x] Task: Analyze Airbnb data missing fields 1a122b4
    - [ ] Run `debug_scrapers.py` for Airbnb.
    - [ ] detailed log of `listingParamOverrides` and `structuredDisplayPrice` for failed items.
    - [ ] Confirm if `guestLabel` or similar fields are available to verify person count.
- [x] Task: Conductor - User Manual Verification 'Diagnosis and Validation' (Protocol in workflow.md) [checkpoint: 2e7738c]

## Phase 2: Scraper Fixes
- [x] Task: Update Booking.com Scraper b2c90ea
    - [ ] Write Tests: Create unit test with a saved HTML snippet (mock) to verify price extraction.
    - [ ] Implement Feature: Update `booking_scraper.py` selectors based on analysis.
    - [ ] Implement Feature: Explicitly parse "total price" and calculate "per night" if necessary.
- [x] Task: Update Airbnb Scraper 743f189
    - [ ] Write Tests: Create unit test with a saved JSON snippet (mock) to verify price and capacity extraction.
    - [ ] Implement Feature: Refine `airbnb_scraper.py` to correctly extract `price` (handling discounts).
    - [ ] Implement Feature: Add extraction for "max guests" and filter out listings that are too small.
- [x] Task: Conductor - User Manual Verification 'Scraper Fixes' (Protocol in workflow.md) [checkpoint: 0c575d3]

## Phase 3: Integration and Verification
- [x] Task: Enforce Pet Filter Validation 5b8e6fc
    - [ ] Write Tests: Add a test case that checks if the "pet friendly" flag is being respected in the agent results.
    - [ ] Implement Feature: Add a post-processing check in `holland_agent.py` (or scrapers) to ensure `pet_friendly=True`.
- [ ] Task: End-to-End Verification
    - [ ] Run `generate_full_html.py` (or the new debug script) and generate a new HTML report.
    - [ ] Manually verify 3-5 links from the report to ensure the price and capacity on the landing page match the report.
- [ ] Task: Conductor - User Manual Verification 'Integration and Verification' (Protocol in workflow.md)
