import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
# We will create this class
from patchright_airbnb_scraper import SmartAirbnbScraper

@pytest.mark.asyncio
async def test_smart_scraper_fallback_logic():
    # Setup mocks for the internal strategies
    scraper = SmartAirbnbScraper()
    
    # We'll mock the internal methods that we'll implement
    scraper._search_curl = AsyncMock(side_effect=Exception("429 Too Many Requests"))
    scraper._search_firecrawl = AsyncMock(return_value=[{"name": "Firecrawl Deal", "price_per_night": 100}])
    scraper._get_fallback_data = MagicMock(return_value=[{"name": "Fallback Deal", "price_per_night": 50}])
    
    # Perform search
    results = await scraper.search_airbnb("Amsterdam", "2026-03-01", "2026-03-05")
    
    # Assertions
    assert len(results) == 1
    assert results[0]["name"] == "Firecrawl Deal"
    scraper._search_curl.assert_called_once()
    scraper._search_firecrawl.assert_called_once()

@pytest.mark.asyncio
async def test_smart_scraper_all_fail():
    scraper = SmartAirbnbScraper()
    
    scraper._search_curl = AsyncMock(side_effect=Exception("Curl failed"))
    scraper._search_firecrawl = AsyncMock(side_effect=Exception("Firecrawl failed"))
    scraper._get_fallback_data = MagicMock(return_value=[{"name": "Fallback Deal", "price_per_night": 50}])
    
    results = await scraper.search_airbnb("Amsterdam", "2026-03-01", "2026-03-05")
    
    assert len(results) == 1
    assert results[0]["name"] == "Fallback Deal"
