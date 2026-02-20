"""
Functional tests for the scraper architecture changes.
Run: python3 tests/test_architecture_changes.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

results = []

def test(name, func):
    try:
        func()
        results.append((name, True, None))
        print(f"  ✓ {name}")
    except Exception as e:
        results.append((name, False, str(e)))
        print(f"  ✗ {name}: {e}")


# === Test 1: StrategyMetrics ===
def test_strategy_metrics():
    from scraper_health import StrategyMetrics
    m = StrategyMetrics(storage_file='/tmp/test_sm.json')
    m.records = []  # Clear
    m.record('airbnb', 'curl-cffi', True, 3.5, result_count=5)
    m.record('airbnb', 'curl-cffi', False, 1.2, error='429')
    m.record('airbnb', 'patchright', True, 15.3, result_count=8)
    
    rate, count = m.get_success_rate('airbnb', 'curl-cffi')
    assert count == 2, f"Expected 2 attempts, got {count}"
    assert rate == 0.5, f"Expected 50% rate, got {rate}"
    
    rate2, count2 = m.get_success_rate('airbnb', 'patchright')
    assert count2 == 1 and rate2 == 1.0
    
    assert m.get_consecutive_failures('airbnb') == 0  # Last was patchright success

test("StrategyMetrics basic", test_strategy_metrics)


# === Test 2: AdaptiveRouter ===
def test_adaptive_router():
    from scraper_health import StrategyMetrics, AdaptiveRouter
    m = StrategyMetrics(storage_file='/tmp/test_ar.json')
    m.records = []
    # Patchright has 100% success, curl-cffi has 0%
    m.record('airbnb', 'curl-cffi', False, 1.0, error='429')
    m.record('airbnb', 'curl-cffi', False, 1.0, error='429')
    m.record('airbnb', 'patchright', True, 15.0, result_count=5)
    m.record('airbnb', 'patchright', True, 12.0, result_count=3)
    
    router = AdaptiveRouter(m)
    order = router.get_strategy_order('airbnb')
    assert order[-1] == 'fallback', f"Fallback should be last: {order}"
    assert order[0] == 'patchright', f"Patchright should be first (100%): {order}"

test("AdaptiveRouter ordering", test_adaptive_router)


# === Test 3: RequestDelayer pressure ===
def test_delayer_pressure():
    from rate_limit_bypass import RequestDelayer
    d = RequestDelayer(min_delay=2, max_delay=5)
    assert d._pressure_level == 0
    d.notify_pressure()
    assert d._pressure_level == 1
    assert d.min_delay == 3.0  # 2 * 1.5
    assert d.max_delay == 7.5  # 5 * 1.5
    d.notify_pressure()
    assert d._pressure_level == 2
    assert d.min_delay == 4.0  # 2 * 2.0
    assert d.max_delay == 10.0  # 5 * 2.0

test("RequestDelayer adaptive pressure", test_delayer_pressure)


# === Test 4: Cache with disk persistence ===
def test_cache():
    from rate_limit_bypass import Cache
    import json
    c = Cache(ttl_minutes=30, disk_file='/tmp/test_cache.json')
    key = c.make_key('airbnb', region='Amsterdam', checkin='2026-02-15')
    c.set(key, [{"name": "Test Deal", "price": 100}])
    
    # Read back from memory
    result = c.get(key)
    assert result is not None, "Cache miss"
    assert result[0]["name"] == "Test Deal"
    
    # Check disk file exists
    assert os.path.exists('/tmp/test_cache.json'), "Disk file not created"
    with open('/tmp/test_cache.json') as f:
        disk_data = json.load(f)
    assert key in disk_data, f"Key {key} not in disk data"

test("Cache with disk persistence", test_cache)


# === Test 5: HealthReport format ===
def test_health_report():
    from scraper_health import StrategyMetrics, HealthReport
    m = StrategyMetrics(storage_file='/tmp/test_hr.json')
    m.records = []
    m.record('airbnb', 'curl-cffi', True, 3.0, result_count=5)
    m.record('booking', 'curl-cffi', True, 2.0, result_count=3)
    
    report = HealthReport(m)
    text = report.generate()
    assert 'SCRAPER HEALTH REPORT' in text
    assert 'AIRBNB' in text
    assert 'BOOKING' in text

test("HealthReport generation", test_health_report)


# === Test 6: ExponentialBackoff cap ===
def test_backoff_cap():
    from rate_limit_bypass import ExponentialBackoff
    b = ExponentialBackoff(max_retries=10, base_delay=10)
    # At attempt 5: 2^5 * 10 = 320, should be capped at 120
    b.attempt = 5
    delay = b.get_delay()
    assert delay <= 130, f"Delay {delay} exceeds cap"  # 120 + max 10 jitter

test("ExponentialBackoff 120s cap", test_backoff_cap)


# === Test 7: SessionWarmer cold/warm check ===
def test_session_warmer():
    from rate_limit_bypass import SessionWarmer
    sw = SessionWarmer()
    assert not sw.is_warm('www.airbnb.com'), "Should be cold initially"
    import time
    sw._warmed_sessions['www.airbnb.com'] = time.time()
    assert sw.is_warm('www.airbnb.com'), "Should be warm after marking"

test("SessionWarmer state tracking", test_session_warmer)


# === Test 8: SmartAirbnbScraper fallback ===
def test_smart_scraper_fallback():
    from airbnb_scraper_enhanced import SmartAirbnbScraper
    scraper = SmartAirbnbScraper()
    fallback = scraper._get_fallback('Amsterdam', '2026-02-15', '2026-02-22', 4)
    assert len(fallback) > 0, "Fallback should return deals"
    assert fallback[0]['source'] == 'airbnb (fallback)'

test("SmartAirbnbScraper fallback", test_smart_scraper_fallback)


# === Test 9: EnhancedAirbnbScraper JSON parsing ===
def test_json_parsing():
    import json as json_mod
    from bs4 import BeautifulSoup
    from airbnb_scraper_enhanced import EnhancedAirbnbScraper
    
    mock_data = {
        "niobeClientData": [[
            "ROOT_QUERY",
            {
                "data": {
                    "presentation": {
                        "staysSearch": {
                            "results": {
                                "searchResults": [
                                    {
                                        "__typename": "StaySearchResult",
                                        "id": "123",
                                        "listing": {
                                            "id": "123",
                                            "title": "Spacious Family Home",
                                            "avgRatingLocalized": "4.8",
                                            "avgRatingA11yLabel": "4.8 out of 5 stars, 50 reviews",
                                            "personCapacity": 4,
                                            "listingUrl": "/rooms/123?adults=4"
                                        },
                                        "structuredDisplayPrice": {
                                            "primaryLine": {
                                                "price": "€200",
                                                "discountedPrice": "€150"
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        ]]
    }
    
    html = f'<html><body><script type="application/json">{json_mod.dumps(mock_data)}</script></body></html>'
    soup = BeautifulSoup(html, 'html.parser')
    
    scraper = EnhancedAirbnbScraper()
    deals = scraper._parse_html(soup, "Amsterdam", "2026-02-15", "2026-02-22", 4)
    assert len(deals) == 1, f"Expected 1 deal, got {len(deals)}"
    assert deals[0]['name'] == 'Spacious Family Home'
    assert deals[0]['price_per_night'] == 150  # Should use discounted price

test("EnhancedAirbnbScraper JSON parsing", test_json_parsing)


# === Test 10: VacationAgent instantiation ===
def test_agent_init():
    from holland_agent import VacationAgent
    agent = VacationAgent(budget_min=40, budget_max=200)
    assert agent.budget_min == 40
    assert agent.budget_max == 200
    assert agent.airbnb_scraper is not None
    assert agent.booking_scraper is not None

test("VacationAgent instantiation", test_agent_init)


# === Summary ===
print()
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f"Results: {passed}/{len(results)} passed, {failed} failed")
if failed:
    print("\nFailed tests:")
    for name, ok, err in results:
        if not ok:
            print(f"  ✗ {name}: {err}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED ✓")
