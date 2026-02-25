import unittest
import os
import sys

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

        # Mock deals with all required fields so only pet filter decides
        mock_deals = [
            {
                "name": "Dog Friendly Villa",
                "location": "Amsterdam",
                "source": "booking.com",
                "url": "https://example.com/dog-friendly",
                "pet_friendly": True,
                "price_per_night": 100,
                "rating": 4.7,
                "reviews": 120,
            },
            {
                "name": "No Pets Apartment",
                "location": "Amsterdam",
                "source": "airbnb",
                "url": "https://example.com/no-pets",
                "pet_friendly": False,
                "price_per_night": 80,
                "rating": 4.4,
                "reviews": 90,
            },
        ]

        agent.all_deals = mock_deals
        validation = agent._validate_deals(pets=1)

        self.assertEqual(validation["total_raw"], 2)
        self.assertEqual(validation["valid_count"], 1)
        self.assertEqual(validation["rejected_count"], 1)
        self.assertEqual(validation["rejected_reasons"].get("not_pet_friendly"), 1)

        self.assertEqual(len(agent.all_deals), 1)
        self.assertEqual(agent.all_deals[0]["name"], "Dog Friendly Villa")


if __name__ == '__main__':
    unittest.main()
