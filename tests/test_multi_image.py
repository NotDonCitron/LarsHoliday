import pytest
import asyncio
import re
from unittest.mock import AsyncMock, MagicMock
from patchright_airbnb_scraper import PatchrightAirbnbScraper
from booking_scraper import BookingScraper

@pytest.mark.asyncio
async def test_airbnb_multi_image_extraction():
    scraper = PatchrightAirbnbScraper()
    # Mock markdown with multiple images and required structure
    markdown = """
![img1](https://test.com/1.jpg)
![img2](https://test.com/2.jpg)
![img3](https://test.com/3.jpg)
### Apartment in Heidelberg
Luxury Loft
€ 700 for 7 nights
https://www.airbnb.com/rooms/12345
"""
    deals = scraper._parse_markdown(markdown, "Heidelberg", 7)
    
    print(f"Deals found: {len(deals)}")
    assert len(deals) > 0
    # We expect an 'images' key with a list
    assert "images" in deals[0]
    assert len(deals[0]["images"]) == 3
    assert deals[0]["images"][0] == "https://test.com/1.jpg?im_w=720"

@pytest.mark.asyncio
async def test_booking_multi_image_extraction():
    scraper = BookingScraper()
    # Mock HTML with multiple images in a card
    html = """
    <div data-testid="property-card">
        <h3 data-testid="title">Grand Hotel</h3>
        <img data-testid="image" src="https://img.com/1.jpg">
        <div class="hidden-images">
            <img src="https://img.com/2.jpg">
            <img src="https://img.com/3.jpg">
        </div>
        <div data-testid="price-and-discounted-price">€ 700</div>
    </div>
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    deals = scraper._parse_html(soup, "Heidelberg", "2026-03-08", "2026-03-15", 7)
    
    assert len(deals) > 0
    assert "images" in deals[0]
    assert len(deals[0]["images"]) == 3
    assert deals[0]["images"][0] == "https://img.com/1.jpg"
