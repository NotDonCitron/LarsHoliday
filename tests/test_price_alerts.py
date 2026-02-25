import pytest
from unittest.mock import AsyncMock, patch

from holland_agent import VacationAgent
from rate_limit_bypass import PriceAlertSystem


def test_price_alert_threshold_dedupe_and_cooldown(tmp_path):
    storage = tmp_path / "price_alerts_test.json"
    alerts = PriceAlertSystem(
        storage_file=str(storage),
        alert_threshold=0.20,
        cooldown_minutes=120,
        dedupe_minutes=10,
        max_history=10,
    )

    # Baseline observation (no alert on first price)
    triggered, message = alerts.track_property(
        property_id="p1",
        name="Test Property",
        price=100.0,
        url="https://example.com/p1",
        source="airbnb",
    )
    assert triggered is False
    assert message == ""

    # Small drop below default threshold -> no alert
    triggered, _ = alerts.track_property(
        property_id="p1",
        name="Test Property",
        price=90.0,
        url="https://example.com/p1",
        source="airbnb",
    )
    assert triggered is False

    # Same price within dedupe window -> no new entry
    before_len = len(alerts.get_history("p1"))
    triggered, _ = alerts.track_property(
        property_id="p1",
        name="Test Property",
        price=90.0,
        url="https://example.com/p1",
        source="airbnb",
    )
    after_len = len(alerts.get_history("p1"))
    assert triggered is False
    assert before_len == after_len

    # Big drop crosses threshold -> alert
    triggered, message = alerts.track_property(
        property_id="p1",
        name="Test Property",
        price=70.0,
        url="https://example.com/p1",
        source="airbnb",
    )
    assert triggered is True
    assert "PRICE ALERT" in message

    # Cooldown+duplicate alert price suppression
    triggered, message = alerts.track_property(
        property_id="p1",
        name="Test Property",
        price=70.0,
        url="https://example.com/p1",
        source="airbnb",
    )
    assert triggered is False
    assert message == ""

    # Threshold override (5%) should trigger for 10% drop
    alerts.track_property(
        property_id="p2",
        name="Override Property",
        price=200.0,
        url="https://example.com/p2",
        source="booking",
    )
    triggered, _ = alerts.track_property(
        property_id="p2",
        name="Override Property",
        price=180.0,
        url="https://example.com/p2",
        source="booking",
        threshold=0.05,
    )
    assert triggered is True


@pytest.mark.asyncio
async def test_price_alert_integration_calls_tracker_with_overrides():
    agent = VacationAgent()
    agent.cache.clear()

    deal = {
        "name": "Test Property",
        "price_per_night": 100,
        "url": "https://test.com/1",
        "source": "test",
        "location": "Amsterdam",
        "pet_friendly": True,
        "rating": 4.6,
        "reviews": 120,
        "currency": "EUR",
        "alert_threshold": 0.08,
        "alert_cooldown_minutes": 30,
    }

    agent.airbnb_scraper.search_airbnb = AsyncMock(return_value=[deal])
    agent.booking_scraper.search_booking = AsyncMock(return_value=[])

    with patch("holland_agent.price_alerts") as mock_alerts:
        mock_alerts.track_property.return_value = (True, "🔔 PRICE ALERT!")
        mock_alerts.get_history.return_value = [{"price": 110}, {"price": 100}]

        results = await agent.find_best_deals(["Amsterdam"], "2026-03-01", "2026-03-05")

        assert "run_id" in results
        assert mock_alerts.track_property.call_count >= 1

        kwargs = mock_alerts.track_property.call_args.kwargs
        assert kwargs["threshold"] == 0.08
        assert kwargs["cooldown_minutes"] == 30
        assert results["price_alerts"]
