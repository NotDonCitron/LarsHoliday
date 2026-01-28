from booking_scraper import BookingScraper
from airbnb_scraper import AirbnbScraper

def verify_links():
    # Setup
    city = "Tokyo"
    checkin = "2026-10-01"
    checkout = "2026-10-07"
    adults = 2
    
    print(f"--- Testing Link Generation for {city} ---")
    print(f"Dates: {checkin} to {checkout}")
    print(f"Adults: {adults}\n")

    # 1. Test Booking.com Fallback Link
    booking = BookingScraper()
    # We explicitly call the fallback method to see what URL it generates
    booking_deals = booking._get_fallback_data(city, checkin, checkout, adults)
    
    if booking_deals:
        deal = booking_deals[0]
        print(f"[Booking.com] Deal Name: {deal['name']}")
        print(f"[Booking.com] Generated URL: {deal['url']}")
        
        # Verification
        if "ss=Tokyo" in deal['url'] and "checkin=2026-10-01" in deal['url']:
            print("✅ Booking.com Link looks CORRECT!\n")
        else:
            print("❌ Booking.com Link looks WRONG.\n")

    # 2. Test Airbnb Fallback Link
    airbnb = AirbnbScraper()
    airbnb_deals = airbnb._get_fallback_data(city, checkin, checkout, adults)
    
    if airbnb_deals:
        deal = airbnb_deals[0]
        print(f"[Airbnb] Deal Name: {deal['name']}")
        print(f"[Airbnb] Generated URL: {deal['url']}")
        
        # Verification
        if "query=Tokyo" in deal['url'] and "checkin=2026-10-01" in deal['url']:
            print("✅ Airbnb Link looks CORRECT!\n")
        else:
            print("❌ Airbnb Link looks WRONG.\n")

if __name__ == "__main__":
    verify_links()
