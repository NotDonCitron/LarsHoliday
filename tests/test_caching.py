import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from holland_agent import VacationAgent

@pytest.mark.asyncio
async def test_agent_caching():
    agent = VacationAgent()
    agent.cache.clear() # Ensure clean state
    
    # Mock the search_single_city method
    agent._search_single_city = AsyncMock(return_value=[{"name": "Cached Deal", "price_per_night": 100}])
    
    # First search
    await agent.find_best_deals(["Amsterdam"], "2026-03-01", "2026-03-05")
    assert agent._search_single_city.call_count == 1
    
    # Second search (should use cache)
    await agent.find_best_deals(["Amsterdam"], "2026-03-01", "2026-03-05")
    assert agent._search_single_city.call_count == 1 # Still 1 because of cache
