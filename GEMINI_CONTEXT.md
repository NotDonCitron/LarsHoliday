# LarsHoliday Project Context - Handover

## Projekt-Ziel
Ein AI-gesteuerter Urlaubs-Planer für Holland (und international), optimiert für 4 Personen + 1 Hund. Gebaut für einen Freund (SAP-Berater).

## Aktueller technischer Stand
- **Backend**: FastAPI (`api.py`) liefert Daten und das Frontend aus.
- **Frontend**: `frontend_dashboard.html` (interaktives Dashboard, Deutsch).
- **Hosting**: Hugging Face Spaces (Docker-Umgebung).
- **Scraping-Strategie**: Hybrid-Modus.
    - **Airbnb**: Nutzt Firecrawl API mit Markdown-Parsing (robust gegen Cloud-Blockaden).
    - **Booking.com**: Nutzt Firecrawl API mit HTML-Parsing.
- **Secrets**: `FIRECRAWL_API_KEY`, `AGENT_BROWSER_SESSION` sind aktiv. `OPENWEATHER_API_KEY` wird aktuell noch als 'false' gemeldet (muss in HF Settings geprüft werden).

## Erreichte Meilensteine
- [x] Repository von 1000+ Dateien auf ~35 bereinigt.
- [x] Cloud-Blockade durch Firecrawl-Integration durchbrochen.
- [x] Links führen direkt zum Angebot (Referrer-anonymisiert).
- [x] Preise sind variabel und erkennen Dollar/Euro inkl. Tausender-Trenner.
- [x] **Bilder-Optimierung**: Echte Inserats-Fotos werden jetzt extrahiert und im Dashboard angezeigt (Fix in Scrapern + Ranker).
- [x] **Preis-Präzision**: Preis-Parsing für Booking & Airbnb massiv verbessert (Erkennung von Gesamt- vs. Nachtpreis).

## Offene Punkte für den nächsten Chat
1. **Validierung**: Überprüfen, ob in der HF-Umgebung alle Preise korrekt ankommen (keine Default-100€ mehr).
2. **Wetter-Integration**: Sicherstellen, dass der `OPENWEATHER_API_KEY` in den HF Settings hinterlegt wird (aktuell fehlt er).
3. **Feinschliff**: Airbnb-Namen im Markdown noch präziser extrahieren (Erste Ansätze implementiert).

## Wichtige Dateien
- `api.py`: Haupteinstiegspunkt Cloud.
- `holland_agent.py`: Orchestriert die Suche.
- `patchright_airbnb_scraper.py`: Der neue Cloud-Scraper für Airbnb.
- `booking_scraper.py`: Der Cloud-Scraper für Booking.
- `frontend_dashboard.html`: Das UI.
