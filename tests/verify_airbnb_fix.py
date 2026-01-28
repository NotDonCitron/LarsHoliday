
from airbnb_scraper import AirbnbScraper

def verify_airbnb_link():
    city = "Tokyo, Japan"
    checkin = "2026-10-01"
    checkout = "2026-10-07"
    adults = 2
    
    print(f"--- Testing Airbnb Link for {city} ---")
    
    scraper = AirbnbScraper()
    # We call _build_airbnb_url directly via the fallback method logic or just verify the method
    # Since _build_airbnb_url is internal, we can access it on the instance
    
    url = scraper._build_airbnb_url(city, checkin, checkout, adults)
    print(f"Generated URL: {url}")
    
    if "/s/Tokyo%2C%20Japan/homes" in url:
        print("✅ Link structure looks CORRECT!")
    else:
        print("❌ Link structure looks WRONG.")

if __name__ == "__main__":
    verify_airbnb_link()
