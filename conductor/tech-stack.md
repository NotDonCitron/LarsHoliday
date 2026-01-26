# Tech Stack - Holland Vacation Deal Finder

## Core Language
- **Python 3.8+**: The primary language for the application logic, scrapers, and GUI.

## Frontend / GUI
- **Tkinter**: The standard Python interface for creating the interactive desktop application.
- **CustomTkinter (Optional)**: To be considered for achieving the "Dark Mode" aesthetic more easily.

## Web Scraping & Data Extraction
- **BeautifulSoup4**: For parsing HTML content from vacation rental sites.
- **curl-cffi**: Used for making stealthy, browser-like requests to avoid bot detection.
- **httpx**: For asynchronous HTTP requests (used in the orchestrator).
- **agent-browser**: A Node.js-based CLI tool used for complex browser automation tasks.

## External APIs
- **OpenWeather API**: To fetch weather forecasts for property locations.
- **Firecrawl API (Optional)**: For enhanced scraping and data crawling capabilities.

## Data Export & Reports
- **ReportLab or FPDF2**: Python libraries for generating PDF reports of vacation deals.

## Environment & Configuration
- **python-dotenv**: For managing API keys and environment variables securely.
