# Enhancement Plan: Rate Limits & Price Alerts

## Focus Areas (User Priority)

1. **Rate Limit Bypass** - Free strategies only
2. **Price Alerts** - Real-time notifications on price drops
3. **No Budget** - All free alternatives

---

## Strategy 1: Rate Limit Bypass (Free)

### Current Problem
- Airbnb blocks after too many requests
- 429 errors when scraping too fast

### Free Solutions

#### A. User-Agent Rotation
```python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)
```

#### B. Request Delays
```python
import asyncio
import random

async def safe_request(session, url):
    # Random delay between requests (5-15 seconds)
    delay = random.uniform(5, 15)
    print(f"Waiting {delay:.1f}s before request...")
    await asyncio.sleep(delay)
    
    response = await session.get(url)
    
    if response.status_code == 429:
        # Exponential backoff on 429
        for i in range(5):
            wait_time = (2 ** i) * 30 + random.uniform(0, 10)
            print(f"429 received. Waiting {wait_time:.1f}s (attempt {i+1})...")
            await asyncio.sleep(wait_time)
            response = await session.get(url)
            if response.status_code != 429:
                break
    
    return response
```

#### C. Browser Fingerprint Rotation (Free)
```python
# Rotate viewport sizes
VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
    {'width': 1280, 'height': 800},
]

# Rotate locales
LOCALES = ['en-US', 'en-GB', 'de-DE', 'nl-NL']
```

#### D. Multiple Search Endpoints
```python
# Use different search URL patterns
SEARCH_URLS = [
    "https://www.airbnb.com/s/{region}/homes",
    "https://www.airbnb.com/s/{region}/vacation-rentals",
    "https://www.airbnb.com/rooms/{region}",
]
```

---

## Strategy 2: Automatic Fallback (Free)

### Fallback Chain
```
curl-cffi (fast) 
    ↓ (on 429)
Patchright (reliable, slow)
    ↓ (on error)
Static Fallback Data (always works)
```

### Implementation
```python
class SmartAirbnbScraper:
    async def search_airbnb(self, region, checkin, checkout, adults):
        strategies = [
            ('curl-cffi', self._search_curl),
            ('patchright', self._search_patchright),
            ('fallback', self._get_fallback_data),
        ]
        
        for name, strategy in strategies:
            try:
                deals = await strategy(region, checkin, checkout, adults)
                if deals and len(deals) > 0:
                    print(f"✓ {name} succeeded: {len(deals)} deals")
                    return {'source': name, 'deals': deals}
            except Exception as e:
                print(f"✗ {name} failed: {e}")
                continue
        
        return {'source': 'none', 'deals': self._get_fallback_data()}
```

---

## Strategy 3: Price Alerts (Free)

### Features
- Track prices over time
- Alert on significant drops (20%+)
- Store history in local JSON/SQLite
- Console notifications

### Implementation
```python
import json
import os
from datetime import datetime
from pathlib import Path

class PriceAlertSystem:
    def __init__(self, storage_file='price_alerts.json'):
        self.storage_file = storage_file
        self.alerts = self._load_alerts()
    
    def _load_alerts(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        return {'properties': {}}
    
    def save_alerts(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.alerts, f, indent=2)
    
    async def track_property(self, property_id, name, current_price, url):
        """Track a property for price changes"""
        props = self.alerts['properties']
        
        if property_id not in props:
            props[property_id] = {
                'name': name,
                'url': url,
                'prices': [],
                'alert_threshold': 0.20,  # 20% drop
                'last_alert': None,
            }
        
        # Record price
        props[property_id]['prices'].append({
            'price': current_price,
            'date': datetime.now().isoformat()
        })
        
        # Check for price drop
        await self._check_price_drop(property_id)
        
        self.save_alerts()
    
    async def _check_price_drop(self, property_id):
        """Alert if price dropped significantly"""
        prop = self.alerts['properties'][property_id]
        prices = prop['prices']
        
        if len(prices) < 2:
            return
        
        old_price = prices[-2]['price']
        new_price = prices[-1]['price']
        
        if old_price > new_price:
            drop_percent = (old_price - new_price) / old_price
            
            if drop_percent >= prop['alert_threshold']:
                msg = (
                    f"🔔 PRICE ALERT!\n"
                    f"Property: {prop['name']}\n"
                    f"Old Price: €{old_price}\n"
                    f"New Price: €{new_price}\n"
                    f"Drop: {drop_percent*100:.1f}%\n"
                    f"URL: {prop['url']}"
                )
                print("\n" + "="*50)
                print(msg)
                print("="*50 + "\n")
                
                prop['last_alert'] = datetime.now().isoformat()
    
    async def get_price_history(self, property_id):
        """Get price history for a property"""
        return self.alerts['properties'].get(property_id, {}).get('prices', [])
    
    async def list_tracked(self):
        """List all tracked properties"""
        print("\n📊 Tracked Properties:")
        print("-" * 50)
        for prop_id, data in self.alerts['properties'].items():
            prices = data['prices']
            if prices:
                latest = prices[-1]
                first = prices[0]
                trend = "📈" if latest['price'] <= first['price'] else "📉"
                print(f"{trend} {data['name']}: €{latest['price']} (tracked since {first['date'][:10]})")
        print()
```

---

## Strategy 4: Caching (Free)

### Implement In-Memory Cache
```python
import asyncio
from datetime import datetime, timedelta
from typing import Optional

class Cache:
    def __init__(self, ttl_minutes=10):
        self.ttl = timedelta(minutes=ttl_minutes)
        self.data = {}
    
    def get(self, key: str) -> Optional[dict]:
        if key in self.data:
            entry, timestamp = self.data[key]
            if datetime.now() - timestamp < self.ttl:
                return entry
            del self.data[key]
        return None
    
    def set(self, key: str, value: dict):
        self.data[key] = (value, datetime.now())

# Global cache
cache = Cache(ttl_minutes=10)

async def cached_search(region, checkin, checkout, adults):
    cache_key = f"airbnb_{region}_{checkin}_{checkout}_{adults}"
    
    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        print(f"⚡ Cache hit for {cache_key}")
        return cached
    
    # Search and cache result
    deals = await real_search(region, checkin, checkout, adults)
    cache.set(cache_key, deals)
    
    return deals
```

---

## Combined Implementation Plan

### Phase 1: Rate Limit Bypass (Free)
1. Add User-Agent rotation
2. Implement request delays (5-15s)
3. Add exponential backoff for 429
4. Rotate browser fingerprints

**Effort**: 2-3 hours

### Phase 2: Smart Fallback
1. Implement fallback chain
2. Test curl-cffi → Patchright → Fallback
3. Log success/failure rates

**Effort**: 2 hours

### Phase 3: Price Alerts
1. Create PriceAlertSystem class
2. Integrate with holland_agent.py
3. Add console notifications
4. Store history in JSON

**Effort**: 3-4 hours

### Phase 4: Caching
1. Implement Cache class
2. Add cache to search methods
3. Set TTL to 10 minutes

**Effort**: 1 hour

---

## Estimated Total Effort

| Phase | Effort | Total |
|-------|--------|-------|
| Phase 1 | 3 hours | |
| Phase 2 | 2 hours | |
| Phase 3 | 4 hours | |
| Phase 4 | 1 hour | |
| **Total** | **~10 hours** | |

---

## Files to Modify

| File | Changes |
|------|---------|
| `airbnb_scraper.py` | Add UA rotation, delays, backoff |
| `patchright_airbnb_scraper.py` | Add to smart fallback |
| `holland_agent.py` | Integrate alerts, caching |
| `price_alerts.py` | New: PriceAlertSystem |
| `cache_utils.py` | New: Cache class |

---

## Success Metrics

- [ ] Zero 429 errors on repeated searches
- [ ] 3+ successful scrapes per minute
- [ ] Price alerts triggered on 20%+ drops
- [ ] Cache hit rate > 50%

---

## Questions

1. Should price alerts be saved to a file or database?
2. Maximum number of properties to track?
3. Alert threshold (default 20%) acceptable?
