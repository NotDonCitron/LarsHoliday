# Airbnb Blocking Problem - Lösung Guide

## Problem Summary

Das **Airbnb Blocking Problem** tritt auf, weil:
1. Airbnb aggressive Bot-Erkennung verwendet
2. `curl-cffi` bietet nur grundlegende Browser-Impersonation
3. Keine Proxy-Rotation
4. Kein CAPTCHA-Handling

## Gefundene Lösungen auf GitHub

### Top Anti-Detection Libraries

| Library | Stars | Pros | Cons |
|---------|-------|------|------|
| **Patchright** | 2,302+ | Vollständig unerkennbar, Playwright-basiert | Schwer, langsamer |
| **Rebrowser Patches** | 1,233+ | Modulär, flexibel | Komplexer Setup |
| **Scrapling** | 8,961+ | Schnell, leicht | Weniger JS-Rendering |
| **Firecrawl** | - | Server-side, API-basiert | Kostenpflichtig |

## Empfohlene Lösung: Patchright

### Warum Patchright?

1. **Vollständige Fingerabdruck-Patching**:
   - Entfernt `navigator.webdriver` Flag
   - Patcht `Runtime.enable` und `Console.enable` Leaks
   - Entfernt Automation-Flags (`--enable-automation`)

2. **Drop-in Playwright-Ersatz**:
   - Gleiche API wie Playwright
   - Einfach zu integrieren

3. **Aktive Community**:
   - Regelmäßige Updates
   - Gute Dokumentation

## Installation

```bash
# Patchright installieren
pip install patchright

# Oder über requirements.txt
echo "patchright" >> requirements.txt
pip install -r requirements.txt
```

## Implementierung

### 1. Neuer Scraper: `patchright_airbnb_scraper.py`

```python
import patchright

class PatchrightAirbnbScraper:
    async def search_airbnb(self, region, checkin, checkout, adults=4):
        # Browser starten (unkontrollierbar erkennbar)
        browser = await patchright.chromium.launch(headless=True)
        
        # Kontext mit realistischem Fingerabdruck
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
        )
        
        page = await context.new_page()
        await page.goto(f'https://www.airbnb.com/s/{region}/homes?checkin={checkin}&checkout={checkout}')
        
        # ... Parsing Logic
        
        await browser.close()
```

### 2. Hybrid-Ansatz (Empfohlen)

```python
# Hybrid-Ansatz: curl-cffi zuerst, Patchright bei 429

class HybridAirbnbScraper:
    async def search_airbnb(self, region, checkin, checkout, adults):
        # 1. Versuche curl-cffi (schnell)
        try:
            deals = await curl_scraper.search(region, checkin, checkout)
            if deals:
                return deals  # Erfolg!
        except:
            pass  # curl-cffi fehlgeschlagen
        
        # 2. Fallback zu Patchright (zuverlässig)
        return await patchright_scraper.search(region, checkin, checkout)
```

### 3. Integration in bestehenden Code

In `holland_agent.py` ändern:

```python
# Statt:
# from airbnb_scraper import AirbnbScraper

# Neu:
try:
    from patchright_airbnb_scraper import HybridAirbnbScraper
    airbnb_scraper = HybridAirbnbScraper()
except ImportError:
    from airbnb_scraper import AirbnbScraper
    airbnb_scraper = AirbnbScraper()
```

## Proxy Rotation (Optional aber Empfohlen)

Für noch bessere Ergebnisse, Proxy-Rotation hinzufügen:

```python
import httpx

class ProxyRotator:
    def __init__(self):
        self.proxies = [
            "http://user:pass@proxy1:8000",
            "http://user:pass@proxy2:8000",
            # ... mehr Proxies
        ]
    
    def get_random_proxy(self):
        return random.choice(self.proxies)
    
    async def fetch_with_proxy(self, url):
        proxy = self.get_random_proxy()
        async with httpx.AsyncClient(proxies=proxy) as client:
            return await client.get(url)
```

### Proxy-Anbieter

| Anbieter | Typ | Preis |
|----------|-----|-------|
| Bright Data | Residential | $15-20/GB |
| SmartProxy | Residential | $12-15/GB |
| Oxylabs | Residential | $18-25/GB |
| Thordata | Residential | $10-15/GB |

## Testen

```bash
# Testen des neuen Scrapers
python patchright_airbnb_scraper.py

# Erwartete Ausgabe:
# Testing Patchright Airbnb Scraper...
# ==================================================
# [Patchright] Navigating to: https://www.airbnb.com/s/amsterdam/homes?checkin=...
# [Patchright] Found 15 properties
#
# #1 - City Center Apartment
#    Location: Amsterdam
#    Price: €145/night
#    Rating: 4.8/5.0 (120 reviews)
```

## Fallback-Strategie

Wenn Patchright auch blockiert:

1. **Firecrawl API** (Server-side Rendering)
   ```python
   from firecrawl import FirecrawlApp
   
   app = FirecrawlApp(api_key="YOUR_KEY")
   result = app.scrape('https://airbnb.com/s/amsterdam/homes')
   ```

2. **Statische Fallback-Daten**
   - Bereits in `patchright_airbnb_scraper.py` implementiert
   - Funktioniert immer

## Zusammenfassung

| Schritt | Aktion | Aufwand |
|---------|--------|---------|
| 1 | `pip install patchright` | 1 Minute |
| 2 | `patchright_airbnb_scraper.py` verwenden | 5 Minuten |
| 3 | Hybrid-Ansatz integrieren | 10 Minuten |
| 4 | (Optional) Proxy-Rotation | 30 Minuten |

**Gesamtdauer**: ~15 Minuten für grundlegende Integration

## Nächste Schritte

1. ✅ Patchright installiert
2. ✅ `patchright_airbnb_scraper.py` erstellt
3. ⏳ In `holland_agent.py` integrieren
4. ⏳ Testen
5. ⏳ (Optional) Proxy-Rotation hinzufügen
