"""
Rate Limit Bypass Utilities
Free strategies to avoid blocking and rate limits.

Features:
- User-Agent rotation (diverse browser mix)
- Adaptive request delays (increase under pressure)
- Exponential backoff
- Browser fingerprint rotation
- Disk-persistent caching (30-min TTL)
- Session warming
- Price alerts
"""

import asyncio
import random
import time
import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

# ============================================================================
# USER-AGENT ROTATION (diverse browser mix for fingerprint variety)
# ============================================================================

USER_AGENTS = [
    # Chrome (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome (Linux)
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
]

BROWSER_VERSIONS = [
    "122.0.0.0",
    "121.0.0.0",
    "120.0.0.0",
    "123.0.0.0",
]

def get_random_user_agent() -> str:
    """Return a random user agent string"""
    return random.choice(USER_AGENTS)

def generate_user_agent() -> str:
    """Generate a realistic user agent with random components"""
    platform = random.choice(['Windows NT 10.0; Win64; x64', 'Macintosh; Intel Mac OS X 10_15_7', 'X11; Linux x86_64'])
    chrome_version = random.choice(BROWSER_VERSIONS)
    return f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"

# ============================================================================
# BROWSER FINGERPRINT ROTATION
# ============================================================================

VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
    {'width': 1280, 'height': 800},
    {'width': 1280, 'height': 720},
]

LOCALES = ['en-US', 'en-GB', 'de-DE', 'nl-NL', 'fr-FR']

PLATFORMS = ['Win32', 'MacIntel', 'Linux x86_64']

def get_random_fingerprint() -> Dict[str, Any]:
    """Return a random browser fingerprint"""
    return {
        'viewport': random.choice(VIEWPORTS),
        'locale': random.choice(LOCALES),
        'platform': random.choice(PLATFORMS),
        'user_agent': get_random_user_agent(),
        'timezone': random.choice(['America/New_York', 'Europe/London', 'Europe/Berlin']),
    }

# ============================================================================
# REQUEST DELAYS
# ============================================================================

class RequestDelayer:
    """
    Adaptive delay manager that increases delays under pressure.
    
    When 429 errors are detected (via notify_pressure), delays increase
    up to 3x the base max. Delays gradually decay back to normal.
    """
    
    def __init__(self, min_delay: float = 5.0, max_delay: float = 15.0):
        self.base_min_delay = min_delay
        self.base_max_delay = max_delay
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time: float = 0.0
        self._pressure_level = 0  # 0 = normal, increases with 429s
        self._last_pressure_time: float = 0.0
    
    def notify_pressure(self):
        """Call when a 429 or rate limit is detected to increase delays."""
        self._pressure_level = min(self._pressure_level + 1, 5)
        self._last_pressure_time = time.time()
        # Scale delays: each pressure level adds 50% to delays
        multiplier = 1.0 + (self._pressure_level * 0.5)
        self.min_delay = self.base_min_delay * multiplier
        self.max_delay = self.base_max_delay * multiplier
    
    def _maybe_decay_pressure(self):
        """Decay pressure if no issues for 5 minutes."""
        if self._pressure_level > 0 and self._last_pressure_time > 0:
            elapsed = time.time() - self._last_pressure_time
            if elapsed > 300:  # 5 minutes of calm
                self._pressure_level = max(0, self._pressure_level - 1)
                multiplier = 1.0 + (self._pressure_level * 0.5)
                self.min_delay = self.base_min_delay * multiplier
                self.max_delay = self.base_max_delay * multiplier
                self._last_pressure_time = time.time()
    
    async def wait(self):
        """Wait before next request with adaptive delays."""
        self._maybe_decay_pressure()
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < self.min_delay:
            delay = random.uniform(self.min_delay, self.max_delay)
            if self._pressure_level > 0:
                print(f"   [Delay] Waiting {delay:.1f}s (pressure level {self._pressure_level})...")
            else:
                print(f"   [Delay] Waiting {delay:.1f}s...")
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    def wait_sync(self):
        """Synchronous wait (for non-async code)"""
        self._maybe_decay_pressure()
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < self.min_delay:
            delay = random.uniform(self.min_delay, self.max_delay)
            if self._pressure_level > 0:
                print(f"   [Delay] Waiting {delay:.1f}s (pressure level {self._pressure_level})...")
            else:
                print(f"   [Delay] Waiting {delay:.1f}s...")
            time.sleep(delay)
        
        self.last_request_time = time.time()

# ============================================================================
# EXPONENTIAL BACKOFF
# ============================================================================

class ExponentialBackoff:
    """
    Implements exponential backoff for rate limit errors.
    
    Uses a lower base delay (10s vs old 30s) with jitter to avoid
    thundering herd while still recovering faster.
    """
    
    def __init__(self, max_retries: int = 5, base_delay: float = 10.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.attempt = 0
    
    def get_delay(self) -> float:
        """Calculate delay for current attempt"""
        # Exponential: 2^attempt * base + random jitter
        # Capped at 120 seconds to avoid absurdly long waits
        delay = min(120.0, (2 ** self.attempt) * self.base_delay)
        jitter = random.uniform(0, min(10.0, delay * 0.3))  # Proportional jitter
        return delay + jitter
    
    async def wait(self):
        """Wait with exponential backoff"""
        delay = self.get_delay()
        print(f"   [Backoff] Waiting {delay:.1f}s (attempt {self.attempt + 1}/{self.max_retries})...")
        await asyncio.sleep(delay)
        self.attempt += 1
    
    def reset(self):
        """Reset attempt counter"""
        self.attempt = 0
    
    def should_retry(self) -> bool:
        """Check if should retry"""
        return self.attempt < self.max_retries

# ============================================================================
# CACHING
# ============================================================================

class Cache:
    """
    In-memory + disk-persistent cache with TTL.
    
    Caches search results in memory with disk backup so results
    survive process restarts within the TTL window.
    """
    
    def __init__(self, ttl_minutes: int = 30, disk_file: str = '.search_cache.json'):
        self.ttl = timedelta(minutes=ttl_minutes)
        self.data = {}
        self.disk_file = disk_file
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Load cached data from disk on startup."""
        if os.path.exists(self.disk_file):
            try:
                with open(self.disk_file, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                for key, entry in raw.items():
                    ts = datetime.fromisoformat(entry['timestamp'])
                    if datetime.now() - ts < self.ttl:
                        self.data[key] = (entry['value'], ts)
            except (json.JSONDecodeError, IOError, KeyError):
                pass
    
    def _save_to_disk(self):
        """Persist cache to disk."""
        try:
            serializable = {}
            for key, (value, ts) in self.data.items():
                serializable[key] = {
                    'value': value,
                    'timestamp': ts.isoformat()
                }
            with open(self.disk_file, 'w', encoding='utf-8') as f:
                json.dump(serializable, f, ensure_ascii=False)
        except (IOError, TypeError):
            pass
    
    def make_key(self, source: str, **kwargs) -> str:
        """Create a cache key from source and search parameters."""
        parts = f"{source}_" + "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return hashlib.md5(parts.encode()).hexdigest()[:16]  # pyre-ignore[6]
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.data:
            value, timestamp = self.data[key]
            if datetime.now() - timestamp < self.ttl:
                print(f"   [Cache] ⚡ HIT")
                return value
            else:
                del self.data[key]  # pyre-ignore[20]
        return None
    
    def set(self, key: str, value: Any):
        """Set cached value and persist to disk."""
        self.data[key] = (value, datetime.now())
        print(f"   [Cache] SET")
        self._save_to_disk()
    
    def clear(self):
        """Clear all cached data"""
        self.data.clear()
        if os.path.exists(self.disk_file):
            os.remove(self.disk_file)
        print("   [Cache] CLEARED")
    
    def cleanup(self):
        """Remove expired entries"""
        expired = [k for k, (v, t) in self.data.items() if datetime.now() - t >= self.ttl]
        for k in expired:
            del self.data[k]  # pyre-ignore[20]
        if expired:
            self._save_to_disk()

# Global cache with 30-minute TTL
cache = Cache(ttl_minutes=30)

# ============================================================================
# PRICE ALERTS
# ============================================================================

class PriceAlertSystem:
    """Track prices and alert on significant drops"""
    
    def __init__(self, storage_file: str = 'price_alerts.json', alert_threshold: float = 0.20):
        self.storage_file = storage_file
        self.alert_threshold = alert_threshold
        self.alerts = self._load_alerts()
    
    def _load_alerts(self) -> dict:
        """Load alerts from file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {'properties': {}}
    
    def _save_alerts(self):
        """Save alerts to file"""
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.alerts, f, indent=2, ensure_ascii=False)
    
    def track_property(
        self,
        property_id: str,
        name: str,
        price: float,
        url: str,
        source: str = "unknown"
    ) -> tuple[bool, str]:
        """
        Track a property price and check for drops.
        
        Returns:
            (alert_triggered: bool, message: str)
        """
        props = self.alerts['properties']
        
        if property_id not in props:
            props[property_id] = {
                'name': name,
                'url': url,
                'source': source,
                'prices': [],
                'alert_threshold': self.alert_threshold,
                'last_alert': None,
            }
        
        prop = props[property_id]
        
        # Record price
        price_entry = {
            'price': price,
            'date': datetime.now().isoformat(),
            'source': source,
        }
        prop['prices'].append(price_entry)
        
        # Check for price drop
        alert_triggered = False
        message = ""
        
        if len(prop['prices']) >= 2:
            old_price = prop['prices'][-2]['price']
            new_price = price
            
            if old_price > new_price:
                drop_percent = (old_price - new_price) / old_price
                
                if drop_percent >= prop['alert_threshold']:
                    message = (
                        f"\n{'='*60}\n"
                        f"🔔 PRICE ALERT! 🔔\n"
                        f"{'='*60}\n"
                        f"Property: {name}\n"
                        f"Previous: €{old_price:.2f}\n"
                        f"Current:  €{new_price:.2f}\n"
                        f"Drop: {drop_percent*100:.1f}%\n"
                        f"Source: {source}\n"
                        f"URL: {url}\n"
                        f"{'='*60}\n"
                    )
                    alert_triggered = True
                    prop['last_alert'] = datetime.now().isoformat()
        
        # Keep only last 10 prices
        if len(prop['prices']) > 10:
            prop['prices'] = prop['prices'][-10:]
        
        self._save_alerts()
        return alert_triggered, message
    
    def get_history(self, property_id: str) -> List[dict]:
        """Get price history for a property"""
        return self.alerts['properties'].get(property_id, {}).get('prices', [])
    
    def list_tracked(self) -> str:
        """List all tracked properties with current prices"""
        if not self.alerts['properties']:
            return "No properties tracked yet.\n"
        
        lines = ["\n📊 Tracked Properties:" + "-"*40]
        for prop_id, data in self.alerts['properties'].items():
            prices = data['prices']
            if prices:
                latest = prices[-1]
                first = prices[0]
                trend = "📈" if latest['price'] <= first['price'] else "📉"
                lines.append(
                    f"{trend} {data['name'][:40]}\n"
                    f"   €{latest['price']:.2f} | tracked since {first['date'][:10]}"
                )
        lines.append("-"*40 + "\n")
        return "\n".join(lines)

# Global price alert system
price_alerts = PriceAlertSystem()

# ============================================================================
# SMART REQUEST (combines all features)
# ============================================================================

class SmartRequester:
    """Combines all rate limit bypass strategies with adaptive behavior."""
    
    def __init__(self):
        self.delayer = RequestDelayer(min_delay=5, max_delay=15)
        self.backoff = ExponentialBackoff(max_retries=5, base_delay=10)
        self.cache = cache
        self.price_alerts = price_alerts
    
    async def request(
        self,
        make_request,  # pyre-ignore[2]
        cache_key: Optional[str] = None,
        use_cache: bool = True
    ) -> Any:
        """
        Make a smart request with all bypass strategies.
        
        Args:
            make_request: Async function that makes the actual request
            cache_key: Optional key for caching
            use_cache: Whether to use cache
            
        Returns:
            Response data
        """
        # Check cache first
        if use_cache and cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        # Wait before request
        await self.delayer.wait()
        
        # Make request with backoff on 429
        while True:
            try:
                result = await make_request()
                
                # Cache successful result
                if use_cache and cache_key:
                    self.cache.set(cache_key, result)  # pyre-ignore[6]
                
                self.backoff.reset()
                return result
                
            except Exception as e:
                error_str = str(e).lower()
                
                if '429' in error_str or 'rate limit' in error_str or 'too many requests' in error_str:
                    self.delayer.notify_pressure()
                    await self.backoff.wait()
                    if not self.backoff.should_retry():
                        raise Exception(f"Max retries exceeded: {e}")
                else:
                    raise

# Global smart requester
smart_requester = SmartRequester()

# ============================================================================
# SESSION WARMING
# ============================================================================

class SessionWarmer:
    """
    Pre-warms sessions by visiting target site homepage first.
    
    Collects cookies and establishes a realistic browsing pattern
    before making search requests.
    """
    
    def __init__(self):
        self._warmed_sessions: Dict[str, float] = {}  # domain -> timestamp
        self._warm_ttl = 300  # 5 minutes
    
    def is_warm(self, domain: str) -> bool:
        """Check if a session has been warmed recently."""
        if domain in self._warmed_sessions:
            elapsed = time.time() - self._warmed_sessions[domain]
            return elapsed < self._warm_ttl
        return False
    
    async def warm_session(self, session, domain: str, impersonate: str = "chrome120"):
        """
        Warm a curl-cffi session by visiting the homepage.
        
        Args:
            session: curl-cffi requests.Session
            domain: Target domain (e.g., 'www.airbnb.com')
            impersonate: Browser to impersonate
        """
        if self.is_warm(domain):
            return
        
        try:
            print(f"   [Warm] Warming session for {domain}...")
            homepage = f"https://{domain}/"
            session.get(
                homepage,
                impersonate=impersonate,
                timeout=15,
                allow_redirects=True
            )
            # Small delay to mimic user browsing
            await asyncio.sleep(random.uniform(1.5, 3.0))
            self._warmed_sessions[domain] = time.time()
            print(f"   [Warm] Session warmed for {domain}")
        except Exception as e:
            print(f"   [Warm] Warning: Could not warm session: {str(e)[:50]}")  # pyre-ignore[6]

# Global session warmer
session_warmer = SessionWarmer()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_search_urls(region: str) -> List[str]:
    """Generate multiple search URL patterns"""
    safe_region = region.replace(' ', '-').lower()
    urls = [
        f"https://www.airbnb.com/s/{safe_region}/homes",
        f"https://www.airbnb.com/s/{safe_region}/vacation-rentals",
        f"https://www.airbnb.com/rooms/{safe_region}",
    ]
    random.shuffle(urls)
    return urls

async def safe_sleep(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """Safe async sleep with random duration"""
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))
