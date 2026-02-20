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

## Aktueller Status (Debug-Modus)
Die App läuft aktuell im **Debug-Modus** (Keine Fallbacks für Bilder/Preise). Dies dient dazu, die Scraper-Qualität live zu validieren. Fehlerhafte Extraktionen werden mit `€0` oder `BILD-LADE-FEHLER` markiert.

## Offene Punkte für den nächsten Chat
1. **Wetter-Integration**: Hinterlegung des `OPENWEATHER_API_KEY` in HF Settings.
2. **Finale Politur**: Zurückkehren zu "schönen" Fallbacks, sobald die Scraper-Logik als 100% stabil bestätigt wurde.

## Wichtige Dateien
- `api.py`: Haupteinstiegspunkt Cloud.
- `holland_agent.py`: Orchestriert die Suche.
- `patchright_airbnb_scraper.py`: Der neue Cloud-Scraper für Airbnb.
- `booking_scraper.py`: Der Cloud-Scraper für Booking.
- `frontend_dashboard.html`: Das UI.
