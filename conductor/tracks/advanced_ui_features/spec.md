# Track: Advanced UI & Export Features

## Objective
Enhance the user experience by adding multi-image support, flexible sorting options, and PDF export functionality to the Web Dashboard.

## Features
1. **Multi-Image Support:**
   - Scrapers (Airbnb & Booking) should capture a list of images instead of just one.
   - Frontend should display images in a carousel or thumbnail gallery.
2. **Advanced Sorting & Filtering:**
   - Sort deals by: Price (Low to High), Rating (High to Low), Weather Score, and Overall Score.
   - Real-time client-side sorting in the Web Dashboard.
3. **PDF Export (Web):**
   - New API endpoint to generate a PDF report from current search results.
   - "Export PDF" button in the Web Dashboard.

## Technical Requirements
- Update `patchright_airbnb_scraper.py` and `booking_scraper.py` to extract up to 5 images.
- Update `api.py` to handle PDF generation requests.
- Use `fpdf2` (already in requirements) for PDF generation.
- Implement sorting logic in `frontend_dashboard.html`.
