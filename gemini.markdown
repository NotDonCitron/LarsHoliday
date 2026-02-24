# Project: AirBnB Automation & Analysis

## Tech Stack
- **Backend:** Python (FastAPI, Scrapers, Analysis)
- **Frontend:** HTML/JS Dashboard (Material Design principles)
- **Scraping:** Patchright (Playwright wrapper), Scrapy-like logic
- **Automation:** Github Actions / Local Scripts

## Development Standards
1. **TEST-DRIVEN DEVELOPMENT (TDD):**
   - ALWAYS write tests before implementation.
   - Run tests iteratively.
   - Use the `tests/` directory for all test files.

2. **INFORMATION-SOURCING (Context-7):**
   - Use the `context7` MCP server for any library/framework documentation.
   - Tool call: `context7:get-library-docs` or similar.

3. **DEEP RESEARCH & ANALYSIS:**
   - Before implementing large features, use the `codebase_investigator` tool to map dependencies.
   - Reference files using the @ symbol for better context resolution.

## Project Structure
- Scrapers: `patchright_airbnb_scraper.py`, `booking_scraper.py`
- Analysis: `deal_ranker.py`, `analyze_booking.py`
- UI: `frontend_dashboard.html`, `gui_app.py`
- Documentation: `PROJECT_ANALYSIS.md`, `ENHANCEMENT_PLAN.md`

## Custom Instructions
- Adhere to the architectural patterns in `conductor/product.md` and `conductor/tech-stack.md`.
- Maintain data integrity as specified in `conductor/tracks/live_data_integrity/plan.md`.
