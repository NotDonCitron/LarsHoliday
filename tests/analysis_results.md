# Scraper Analysis Results

## Booking.com
- **Status:** Fails to scrape live data due to anti-bot challenge (Akamai/CAPTCHA).
- **Price Discrepancy:** The code assigns the extracted price to `price_per_night`. However, Booking.com search results typically display the **total price** for the stay. This leads to inflated nightly rates in the application logic.
- **Action Item:** Rename the field to `total_price` in the scraper and calculate `price_per_night` by dividing by the number of nights.

## Airbnb
- **Status:** Fails to extract `propertyId` for some listings, causing them to be skipped.
- **Fallbacks:** Both scrapers rely heavily on fallback data when parsing fails, which masks the underlying issues.
