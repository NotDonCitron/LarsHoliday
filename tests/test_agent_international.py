
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from holland_agent import VacationAgent

@pytest.mark.asyncio
async def test_international_search_flow():
    # Mock Scrapers
    with patch('holland_agent.BookingScraper') as MockBooking, \
         patch('holland_agent.AirbnbScraper') as MockAirbnb, \
         patch('holland_agent.WeatherIntegration') as MockWeather:
        
        # Setup Mocks
        booking_instance = MockBooking.return_value
        booking_instance.search_booking = AsyncMock(return_value=[
            {"name": "Hotel Berlin", "location": "Berlin", "price_per_night": 100, "rating": 4.5, "pet_friendly": True, "source": "booking"}
        ])
        
        airbnb_instance = MockAirbnb.return_value
        airbnb_instance.search_airbnb = AsyncMock(return_value=[
            {"name": "Berlin Apartment", "location": "Berlin", "price_per_night": 90, "rating": 4.8, "pet_friendly": True, "source": "airbnb"}
        ])
        
        weather_instance = MockWeather.return_value
        weather_instance.enrich_deals_with_weather = AsyncMock(side_effect=lambda deals, cities: deals)
        
        # Run Agent
        agent = VacationAgent()
        results = await agent.find_best_deals(
            cities=["Berlin"], 
            checkin="2026-06-01", 
            checkout="2026-06-07",
            pets=1
        )
        
        # Verify
        assert len(results["top_10_deals"]) > 0
        assert results["search_params"]["cities"] == ["Berlin"]
        
        # Check that center parcs logic didn't inject Dutch parks for Berlin
        # We need to inspect the 'all_deals' or look at the source of results
        sources = [d['source'] for d in results['top_10_deals']]
        assert "center-parcs" not in sources
        
        # Verify calls
        booking_instance.search_booking.assert_called_with("Berlin", "2026-06-01", "2026-06-07", 4)
