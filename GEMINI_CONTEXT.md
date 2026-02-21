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
- [x] **Bilder-Optimierung**: Echte Inserats-Fotos werden extrahiert und im Dashboard angezeigt.
- [x] **Preis-Präzision**: Intelligente Umrechnung von Gesamt- in Nachtpreise (Airbnb & Booking).
- [x] **Erweiterte Suche**: Filter für Erwachsene, Kinder, Hunde und dynamisches Budget (pro Nacht/Gesamt).
- [x] **Robustes Airbnb-Parsing**: Umstellung auf Block-Parsing zur Vermeidung von Daten-Mischmasch.
- [x] **Verfügbarkeits-Fix (Incident 0001563/2026)**: Ergebnisse werden nun strikt auf Verfügbarkeit geprüft (Preis-Check + "Sold out" Erkennung).

## Aktueller Status
Die App wurde nach Lars' Feedback stabilisiert. Der Debug-Modus (Anzeige von Objekten ohne Preis) wurde deaktiviert. Es werden nur noch echte, verfügbare Deals für den gewählten Zeitraum angezeigt. 

## Offene Punkte für den nächsten Chat
1. **Wetter-Integration**: Hinterlegung des `OPENWEATHER_API_KEY` in HF Settings.
2. **Performance**: Prüfung, ob Firecrawl-Scraping durch Parallelisierung noch beschleunigt werden kann (aktuell bereits city-parallel).

## Wichtige Dateien
- `api.py`: Haupteinstiegspunkt Cloud.
- `holland_agent.py`: Orchestriert die Suche.
- `patchright_airbnb_scraper.py`: Der neue Cloud-Scraper für Airbnb.
- `booking_scraper.py`: Der Cloud-Scraper für Booking.
- `frontend_dashboard.html`: Das UI.
