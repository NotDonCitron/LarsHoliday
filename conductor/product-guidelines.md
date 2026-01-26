# Product Guidelines - Holland Vacation Deal Finder

## Interaction Tone
- **Professional and Concise:** The application should provide information efficiently without unnecessary conversational filler.
- **Direct Feedback:** Use clear, straightforward language for status updates (e.g., "Search complete," "Exporting PDF...").

## Visual Identity (GUI)
- **Primary Theme:** **Dark Mode.** The interface should utilize a dark background with light, high-contrast text for comfortable viewing.
- **Layout:**
    - **Sidebar:** A dedicated sidebar must be present to display the user's "Favorites" list, keeping them accessible during active searches.
    - **Main Area:** Clear, card-based presentation of property deals with prominent "Book Now" or "More Info" links.

## Data Presentation & Quality
- **Graceful Fallbacks:** If live data cannot be fetched (e.g., due to scraper blocks), the application MUST display fallback/estimated data.
- **Transparency:** Fallback data must be clearly labeled (e.g., "Estimated Price," "Fallback Data") to maintain user trust.
- **Export Format:** **PDF.** The primary format for sharing and portability will be a generated PDF report, styled consistently with the application's clean aesthetic.

## Feature Implementation Guidelines
- **Dog Toggle:** The GUI must include a prominent and functional toggle for "Allow Dogs."
- **Data Integrity:** Pricing and capacity information must be validated against the source wherever possible before being displayed to the user.
