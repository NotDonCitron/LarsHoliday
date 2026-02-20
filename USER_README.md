# Vacation Deal Finder - Benutzeranleitung

## Schnellstart

### Schritt 1: API-Key einrichten (KOSTENLOS)

1. Gehe zu **https://openweathermap.org/api**
2. Klicke auf "Sign Up" und erstelle einen kostenlosen Account
3. Nach der Anmeldung findest du deinen API-Key im Dashboard
4. Kopiere den API-Key

### Schritt 2: Konfiguration

1. Benenne die Datei `.env.example` um zu `.env`
2. Öffne die Datei mit einem Texteditor (Notepad)
3. Ersetze `your_openweather_api_key_here` mit deinem API-Key:
   ```
   OPENWEATHER_API_KEY=dein_key_hier
   ```
4. Speichere die Datei

### Schritt 3: Programm starten

- Doppelklick auf `VacationDealFinder.exe`
- Falls Windows eine Warnung zeigt:
  - Klicke auf "Weitere Informationen"
  - Dann auf "Trotzdem ausführen"

---

## Verwendung

### Suchparameter eingeben

| Feld | Beschreibung | Beispiel |
|------|--------------|----------|
| **Destinations** | Städte oder Regionen (Komma-getrennt) | `Amsterdam, Berlin, Ardennes` |
| **Check-in** | Anreisedatum (YYYY-MM-DD) | `2026-02-15` |
| **Check-out** | Abreisedatum (YYYY-MM-DD) | `2026-02-22` |
| **Adults** | Anzahl Erwachsene | `4` |
| **Max Budget** | Maximale Kosten pro Nacht (EUR) | `250` |
| **Allow Dogs** | Hundefreundliche Unterkünfte | Häkchen setzen |

### Suche starten

1. Klicke auf **"Search Best Deals"**
2. Warte auf die Ergebnisse (kann 1-2 Minuten dauern)
3. Die besten Deals werden in der Liste angezeigt

### Ergebnisse nutzen

- **Open HTML Report**: Öffnet detaillierte Übersicht im Browser
- **Export PDF**: Speichert Ergebnisse als PDF-Datei
- Klicke auf einen Deal, um mehr Details zu sehen

---

## Häufige Probleme

### "Keine Ergebnisse gefunden"

**Lösungen:**
- Prüfe, ob das Datum in der Zukunft liegt
- Erhöhe das Budget
- Probiere andere Städte
- Prüfe die Internetverbindung

### "Wetter-Daten konnten nicht geladen werden"

**Lösungen:**
- Prüfe, ob der API-Key korrekt in `.env` eingetragen ist
- Warte 10 Minuten nach der Registrierung (Key muss aktiviert werden)
- Prüfe die Internetverbindung

### "Programm startet nicht"

**Lösungen:**
- Windows Defender: "Weitere Informationen" → "Trotzdem ausführen"
- Als Administrator ausführen (Rechtsklick → "Als Administrator ausführen")
- Prüfe, ob Antivirus das Programm blockiert

### "Fehler beim Suchen"

**Lösungen:**
- Internetverbindung prüfen
- Andere Städte probieren
- Programm neu starten

---

## Systemanforderungen

- **Betriebssystem**: Windows 10 oder 11
- **Internet**: Erforderlich für Suche
- **Speicher**: ca. 100 MB

---

## Tipps für die besten Deals

1. **Wochentage sind günstiger**: Dienstag-Donnerstag oft 30% billiger
2. **Schulferien vermeiden**: Kurz davor oder danach buchen
3. **Last-Minute**: 7 Tage vorher oft die besten Preise
4. **Center Parcs**: Hunde bleiben meist kostenlos
5. **Wetter beachten**: Frühling/Sommer haben besseres Wetter

---

## Support

Bei Problemen wende dich an den Absender dieser Software.

---

## Technische Informationen

- **Version**: 1.0
- **Quellen**: Booking.com, Airbnb, Center Parcs
- **Wetter**: OpenWeather API
