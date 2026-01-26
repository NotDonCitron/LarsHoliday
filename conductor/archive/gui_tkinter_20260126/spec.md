# Specification: Implement Interactive Tkinter GUI

## 1. Overview
This track involves building a desktop Graphical User Interface (GUI) using Python's built-in `tkinter` library. The GUI will serve as a user-friendly frontend for the existing `HollandVacationAgent`. It allows users to input search parameters (cities, dates, group size, budget) and initiates the search process without using the command line.

## 2. Goals
- **Accessibility:** Remove the need for CLI interaction for end-users.
- **Input Validation:** Ensure users provide valid dates and logical parameters before starting a search.
- **Pet-Friendliness:** Provide a prominent, dedicated toggle to "Allow Dogs" that defaults to checked or forces pet-friendly filtering.
- **Visual Feedback:** Show search progress and simple status updates.

## 3. User Interface Design
### 3.1 Main Window
- **Theme:** Dark Mode (Dark background, light text) as per Product Guidelines.
- **Title:** "Holland Vacation Deal Finder"
- **Layout:**
    - **Input Section:**
        - **Cities:** Text entry (comma-separated). Default: "Amsterdam, Rotterdam, Zandvoort".
        - **Check-in Date:** Date picker or Text entry (YYYY-MM-DD).
        - **Check-out Date:** Date picker or Text entry (YYYY-MM-DD).
        - **Adults:** Spinbox or Entry (Default: 4).
        - **Budget (Max/Night):** Slider or Entry (Default: €250).
        - **Pet Toggle:** Checkbox "Allow Dogs" (Checked by default).
    - **Action Section:**
        - **Search Button:** Large, prominent button to start the process.
    - **Status Section:**
        - **Log/Status Area:** Text area or Label to show "Searching Booking.com...", "Found 15 deals", etc.
    - **Results Section:**
        - **Sidebar:** "Favorites" list (Placeholder for future persistence track).
        - **Main View:** Simplified list of found deals or a button to "Open HTML Report" once finished.

## 4. Functional Requirements
### 4.1 Integration
- The GUI must import and use `HollandVacationAgent` from `holland_agent.py`.
- It should run the `find_best_deals` method asynchronously (or in a separate thread) to avoid freezing the UI during the search.

### 4.2 Error Handling
- **Invalid Dates:** Check that check-out is after check-in.
- **Missing Fields:** Ensure required fields are not empty.
- **Agent Errors:** Capture exceptions from the agent and display a friendly error message in the status area.

## 5. Deliverables
- `gui_app.py`: The main entry point for the GUI application.
- `requirements.txt`: Updated if any new UI-specific libraries are needed (Tkinter is standard, but `tkcalendar` might be useful).
