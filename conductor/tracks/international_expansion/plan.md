# Implementation Plan - International Expansion

## Phase 1: Scraper Refactoring
- [x] Task: Refactor Booking.com Scraper for dynamic locations 21a0b0a
    - [x] Update `booking_scraper.py` to accept a generic location query instead of pre-defined cities.
    - [x] Verify URL construction for international destinations.
- [x] Task: Refactor Airbnb Scraper for dynamic locations 21a0b0a
    - [x] Update `airbnb_scraper.py` to handle generic location inputs.
- [x] Task: Update Agent Logic (`holland_agent.py`) 21a0b0a
    - [x] Rename/Refactor methods that reference "Holland" specifically to be generic.

## Phase 2: GUI & CLI Adaptation
- [x] Task: Update CLI Arguments 21a0b0a
    - [x] Ensure `main.py` accepts country/region parameters if necessary.
- [x] Task: Update GUI Input 21a0b0a
    - [x] Change label from "Cities" to "Destination / Cities".
    - [x] Allow comma-separated lists of arbitrary places.

## Phase 3: Integration & Validation
- [x] Task: Verify International Search f85d977
    - [x] Test searching for a location in Germany (e.g., "Winterberg").
    - [x] Test searching for a location in Belgium (e.g., "Ardennes").
- [x] Task: Conductor - User Manual Verification 'International Expansion' (Protocol in workflow.md) [checkpoint: f85d977]

## Phase 4: Reliability Refinements
- [x] Task: Fix Airbnb Deep Links
    - [x] Update `airbnb_scraper.py` to use stable "Region Search" URLs.
    - [x] Verified that this format bypasses the 503 "Ice Cream" error.
    - [x] Final strategy: Link to the region's search results with pre-filled dates.