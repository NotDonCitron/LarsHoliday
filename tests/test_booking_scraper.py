import unittest
from bs4 import BeautifulSoup
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from booking_scraper import BookingScraper

class TestBookingScraper(unittest.TestCase):
    def test_price_normalization(self):
        """
        Test that the scraper correctly calculates price per night 
        when the website displays total price.
        """
        scraper = BookingScraper()
        
        # Mock HTML with a price of €700
        # This simulates a 7-night stay
        html = """
        <html>
            <body>
                <div data-testid="property-card">
                    <div data-testid="title">Test Hotel</div>
                    <span data-testid="price-and-discounted-price">€ 700</span>
                    <div data-testid="review-score">8.0</div>
                    <div data-testid="review-count">100 reviews</div>
                    <a href="/hotel/test.html">Link</a>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # We need to modify the scraper to accept 'nights' or similar
        # For this test, we assume we will pass 'nights=7' to _parse_html
        # But the current signature doesn't support it, so we call it as is
        # and expect it to fail if we assert the normalized price (100)
        # vs the raw price (700).
        
        # NOTE: This test anticipates the API change to _parse_html(soup, city, nights=1)
        # Since we haven't changed the code yet, we expect this call to fail or return 700.
        
        try:
            # Future signature: _parse_html(soup, city, nights=7)
            deals = scraper._parse_html(soup, "Amsterdam", nights=7)
        except TypeError:
            # Fallback for current signature
            deals = scraper._parse_html(soup, "Amsterdam")
            
        self.assertTrue(len(deals) > 0)
        deal = deals[0]
        
        # If we passed 7 nights and total was 700, per night should be 100
        self.assertEqual(deal['price_per_night'], 100, 
                         f"Expected 100 per night (700/7), got {deal['price_per_night']}")

if __name__ == '__main__':
    unittest.main()
