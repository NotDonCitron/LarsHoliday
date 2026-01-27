# Track: Persistence (Favorites)

## Goal
Allow users to "Star" or "Favorite" specific deals in the GUI and have them persist across sessions.

## Scope
- **Backend:** Simple JSON storage (`favorites.json`).
- **GUI:**
    - Add "Add to Favorites" button/icon to search results.
    - Populate the "Favorites" Sidebar.
    - Allow removing items from Favorites.
    - Clicking a favorite opens the link or shows details.

## Data Structure
- `favorites.json`: List of deal objects (Title, Price, Link, Date Added).
