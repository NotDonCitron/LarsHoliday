import pytest
from airbnb_scraper import AirbnbScraper
from urllib.parse import quote

class TestAirbnbInternational:
    def test_url_construction_special_chars(self):
        scraper = AirbnbScraper()
        # Test city with spaces and special characters
        region = "München, Germany"
        checkin = "2026-06-01"
        checkout = "2026-06-07"
        adults = 2
        
        url = scraper._build_airbnb_url(region, checkin, checkout, adults)
        
        # Verify the URL handles the region correctly (should be encoded or safe)
        # Airbnb URLs can be complex.
        # If the implementation changes to use ?query=..., we should check that.
        # If it keeps /s/{region}/homes, it MUST be encoded.
        
        # We expect "M%C3%BCnchen%2C%20Germany" or similar if in path
        assert " " not in url, "URL should not contain spaces"
        
    def test_fallback_logic_international(self):
        scraper = AirbnbScraper()
        # "Paris" is not in the hardcoded fallback list
        fallback_data = scraper._get_fallback_data("Paris")
        
        # Should not default to Amsterdam properties
        assert fallback_data[0]['location'] != "Amsterdam Centrum", \
            "Fallback for Paris should not be Amsterdam"
