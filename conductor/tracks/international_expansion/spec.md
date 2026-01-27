# Track: International Expansion & Location Flexibility

## Goal
Allow users to search for vacation deals in any location (e.g., Belgium, Germany, France), removing the restriction to just "Holland" or specific hardcoded lists.

## Scope
- Refactor Scrapers (`airbnb_scraper.py`, `booking_scraper.py`, `holland_agent.py`) to accept dynamic location queries.
- Update `main.py` CLI to handle broader search terms.
- Update `gui_app.py` to allow free-text location input or country selection.
- Ensure "Dog Friendly" filter works globally.

## Key Changes
- **Scrapers:** Must handle diverse URL structures or query parameters for different countries/regions.
- **GUI:** Change "Cities" input to a more generic "Destination" or "Region" input.
