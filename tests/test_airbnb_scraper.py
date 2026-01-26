import unittest
from bs4 import BeautifulSoup
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from airbnb_scraper import AirbnbScraper

class TestAirbnbScraper(unittest.TestCase):
    def test_parsing_logic(self):
        """
        Test that the scraper correctly extracts price and filters by capacity.
        """
        scraper = AirbnbScraper()
        
        # Mock Airbnb JSON structure
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
                                                "title": " Spacious Family Home",
                                                "avgRatingLocalized": "4.8",
                                                "avgRatingA11yLabel": "4.8 out of 5 stars, 50 reviews",
                                                "personCapacity": 4
                                            },
                                            "structuredDisplayPrice": {
                                                "primaryLine": {
                                                    "price": "$200",
                                                    "discountedPrice": "$150"
                                                }
                                            },
                                            "listingParamOverrides": {
                                                "id": "123"
                                            }
                                        },
                                        {
                                            "__typename": "StaySearchResult",
                                            "id": "456",
                                            "listing": {
                                                "id": "456",
                                                "title": "Tiny Studio",
                                                "avgRatingLocalized": "4.5",
                                                "avgRatingA11yLabel": "10 reviews",
                                                "personCapacity": 2 
                                            },
                                            "structuredDisplayPrice": {
                                                "primaryLine": {
                                                    "price": "$100"
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
        
        html = f"""
        <html>
            <body>
                <script type="application/json">{json.dumps(mock_data)}</script>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # We expect the scraper to filter out the studio (capacity 2) if we ask for 4 adults
        # Current signature: _parse_html(soup, region)
        # We need to update it to _parse_html(soup, region, required_capacity=4)
        
        try:
            deals = scraper._parse_html(soup, "Amsterdam", required_capacity=4)
        except TypeError:
            deals = scraper._parse_html(soup, "Amsterdam")
            
        # Assertion for filtering (Red phase: currently it returns both)
        # If the code hasn't been updated, it will return 2 deals.
        # We WANT it to return 1 deal (the family home).
        
        # Also check price extraction (should be 150, not 200)
        found_deal = next((d for d in deals if d['name'].strip() == "Spacious Family Home"), None)
        
        if found_deal:
             self.assertEqual(found_deal['price_per_night'], 150, "Should use discounted price")
        
        # The real test for this task is the capacity filtering
        self.assertEqual(len(deals), 1, f"Expected 1 deal (filtered by capacity), got {len(deals)}")

if __name__ == '__main__':
    unittest.main()
