import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from booking_scraper import BookingScraper

@pytest.mark.asyncio
async def test_booking_scraper_fallback_logic():
    scraper = BookingScraper()
    
    scraper._search_curl = AsyncMock(side_effect=Exception("Blocked"))
    scraper._search_firecrawl = AsyncMock(return_value=[{"name": "Booking Firecrawl Deal", "price_per_night": 120}])
    scraper._get_fallback_data = MagicMock(return_value=[{"name": "Booking Fallback", "price_per_night": 80}])
    
    results = await scraper.search_booking("Amsterdam", "2026-03-01", "2026-03-05")
    
    assert len(results) == 1
    assert results[0]["name"] == "Booking Firecrawl Deal"
    scraper._search_curl.assert_called_once()
    scraper._search_firecrawl.assert_called_once()
