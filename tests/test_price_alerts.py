import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from holland_agent import VacationAgent

@pytest.mark.asyncio
async def test_price_alert_integration():
    agent = VacationAgent()
    agent.cache.clear()
    
    # Mock the scrapers to return a specific deal
    deal = {
        "name": "Test Property",
        "price_per_night": 100,
        "url": "https://test.com/1",
        "source": "test",
        "location": "Amsterdam",
        "pet_friendly": True
    }
    
    agent.airbnb_scraper.search_airbnb = AsyncMock(return_value=[deal])
    agent.booking_scraper.search_booking = AsyncMock(return_value=[])
    
    # Mock the price alert system
    with patch('holland_agent.price_alerts') as mock_alerts:
        mock_alerts.track_property.return_value = (True, "🔔 PRICE ALERT!")
        
        results = await agent.find_best_deals(["Amsterdam"], "2026-03-01", "2026-03-05")
        
        # Verify that track_property was called for the deal
        mock_alerts.track_property.assert_called()
        # The result should contain the alert or it should have been printed
