from airbnb_scraper import AirbnbScraper
from bs4 import BeautifulSoup
import json

def verify_live_url_structure():
    scraper = AirbnbScraper()
    checkin = "2026-10-01"
    checkout = "2026-10-07"
    adults = 2
    
    # Mock some HTML content that resembles what Airbnb returns
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
                                        "listing": {"id": "12345", "title": "Test House"},
                                        "structuredDisplayPrice": {"primaryLine": {"price": "$100"}},
                                        "avgRatingLocalized": "4.8",
                                        "avgRatingA11yLabel": "10 reviews"
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
    
    deals = scraper._parse_html(soup, "Test City", checkin, checkout, required_capacity=adults)
    
    if not deals:
        print("❌ Failed to parse mock data")
        return

    deal = deals[0]
    print(f"Generated URL: {deal['url']}")
    
    # We now expect check_in_date and check_out_date
    expected_part = f"check_in_date={checkin}&check_out_date={checkout}&adults={adults}"
    
    if expected_part in deal['url']:
        print("✅ Live URL includes CORRECT search parameters!")
    else:
        print(f"❌ Live URL missing/incorrect parameters. Expected to contain: {expected_part}")

if __name__ == "__main__":
    verify_live_url_structure()