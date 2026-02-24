# Implementation Plan: Advanced UI & Export Features

## Phase 1: Multi-Image Support (Scrapers)
- [ ] Create TDD test for multi-image extraction in `tests/test_multi_image.py`.
- [ ] Update `patchright_airbnb_scraper.py` to extract image list.
- [ ] Update `booking_scraper.py` to extract image list.
- [ ] Update `frontend_dashboard.html` to render a simple image carousel.

## Phase 2: Advanced Sorting
- [ ] Create TDD test for sorting logic in `tests/test_sorting.py`.
- [ ] Add sorting dropdown to `frontend_dashboard.html`.
- [ ] Implement JavaScript sorting logic for the deals grid.

## Phase 3: PDF Export (Web)
- [ ] Create TDD test for PDF generation endpoint in `tests/test_pdf_api.py`.
- [ ] Implement `/export-pdf` endpoint in `api.py`.
- [ ] Add "Export PDF" button to `frontend_dashboard.html`.

## Phase 4: Final Polishing
- [ ] Final visual check of the carousel and dashboard layout.
- [ ] Verify all TDD tests pass.
- [ ] Solicit user blessing for push.
