import unittest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from holland_agent import HollandVacationAgent

class TestAgentValidation(unittest.TestCase):
    def test_pet_filter_enforcement(self):
        """
        Test that the agent filters out any non-pet-friendly deals 
        if the user requested pet-friendly accommodations.
        """
        agent = HollandVacationAgent()
        
        # Mock deals from different sources
        mock_deals = [
            {
                "name": "Dog Friendly Villa",
                "pet_friendly": True,
                "price_per_night": 100,
                "source": "booking.com"
            },
            {
                "name": "No Pets Apartment",
                "pet_friendly": False,
                "price_per_night": 80,
                "source": "airbnb"
            }
        ]
        
        # Patch the internal search method to return our mock deals
        with patch.object(HollandVacationAgent, '_search_single_city', return_value=asyncio.Future()):
             # We need to manually populate all_deals and run validation
             agent.all_deals = mock_deals
             
             # Call validation (which we will implement)
             # Future signature: agent._validate_deals(pets=1)
             try:
                 agent._validate_deals(pets=1)
             except AttributeError:
                 # If not implemented, it won't filter
                 pass
             
             # Assertions
             self.assertEqual(len(agent.all_deals), 1, "Should have filtered out the non-pet-friendly deal")
             self.assertEqual(agent.all_deals[0]['name'], "Dog Friendly Villa")

if __name__ == '__main__':
    unittest.main()
