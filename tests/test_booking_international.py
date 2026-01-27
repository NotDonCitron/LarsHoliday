
import pytest
from booking_scraper import BookingScraper
from urllib.parse import parse_qs, urlparse

class TestBookingInternational:
    def test_url_construction_special_chars(self):
        scraper = BookingScraper()
        # Test city with spaces and special characters
        city = "München, Germany"
        checkin = "2026-06-01"
        checkout = "2026-06-07"
        adults = 2
        
        url = scraper._build_booking_url(city, checkin, checkout, adults)
        
        # Parse the URL to check parameters
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Verify 'ss' parameter is correctly present and likely encoded
        # parse_qs decodes it, so we expect the original string
        assert params['ss'][0] == "München, Germany"
        
        # Check if the URL string itself (before parsing) was actually encoded
        # We expect "M%C3%BCnchen%2C%20Germany" or similar in the raw string, 
        # NOT "München, Germany" literally if we want to be safe, 
        # though modern browsers/libraries handle it. 
        # BUT `curl_cffi` session.get(url) expects a valid URL.
        # If we pass f"ss={city}" and city has spaces, it might break.
        
        assert " " not in url, "URL should not contain spaces"

    def test_fallback_logic_international(self):
        scraper = BookingScraper()
        # "Berlin" is not in the hardcoded fallback list
        fallback_data = scraper._get_fallback_data("Berlin")
        
        # Current behavior: defaults to Amsterdam
        # Desired behavior: Should not strictly default to Amsterdam if we want international support,
        # OR at least the data should reflect it's a fallback.
        # For this test, let's just observe the current behavior.
        # If I change it, I want this test to verify the new behavior (e.g., return empty or generic).
        
        # If I want to fail this test based on "It returns Amsterdam for Berlin", I can do:
        assert fallback_data[0]['location'] != "Zandvoort, near Amsterdam", \
            "Fallback for Berlin should not be Amsterdam"
