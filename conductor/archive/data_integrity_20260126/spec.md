# Specification: Fix Data Integrity Issues

## 1. Overview
This track focuses on resolving critical data accuracy issues identified in the current scraper implementations (`booking_scraper.py` and `airbnb_scraper.py`). Users have reported discrepancies in pricing and person counts. Additionally, this track will strictly enforce the "Allow Dogs" filter in the search logic to ensuring that the results are truly pet-friendly.

## 2. Goals
- **Fix Pricing Accuracy:** Ensure the scraped price reflects the actual booking price for the specified group size and dates.
- **Fix Person Count:** Verify that the "per person" calculation and displayed group capacity are correct.
- **Enforce Pet Policy:** Guarantee that all returned results explicitly allow dogs.
- **Improve Scraper Robustness:** Minimize "NoneType" errors and fallback reliance by improving data extraction logic.

## 3. Detailed Requirements

### 3.1 Booking.com Scraper (`booking_scraper.py`)
- **Price Extraction:** Validate the selector logic for price. Ensure it captures the total price for the *entire* stay, not per night if the display is ambiguous, and correctly parses the currency.
- **Group Size:** Verify that the search URL parameters (`group_adults`, `no_rooms`) are correctly being respected by the returned results.
- **Pet Filter:** Confirm the `nflt=hotelfacility=4` (or equivalent) parameter is effectively filtering for pet-friendly properties.

### 3.2 Airbnb Scraper (`airbnb_scraper.py`)
- **Price Logic:** Investigate `structuredDisplayPrice` and `price_line` extraction. Ensure handling of "discountedPrice" vs. "originalPrice" is correct.
- **Person Capacity:** Extract the listing's max guest capacity to ensure it meets the user's requirement (e.g., "4 adults").
- **Pet Filter:** Verify the `pets=1` parameter is active and working.

### 3.3 Data Model
- **Validation:** Add a validation step in `holland_agent.py` or the scrapers to discard results that do not meet the critical criteria (e.g., price is 0, capacity < group size).

## 4. Non-Functional Requirements
- **Error Handling:** Scrapers should log specific warnings when data is missing but continue processing other items.
- **Performance:** Maintain the current performance; fixes should not significantly slow down the scraping process.

## 5. User Interface Impact
- **HTML Report:** The generated `holland_alle_optionen.html` should accurately reflect the verified prices and person counts.
