
from urllib.parse import quote
from curl_cffi import requests
from bs4 import BeautifulSoup
import re

def verify_google_bypass():
    # Simulate the button click for "Cityden Amsterdam West"
    property_name = "Cityden Amsterdam West"
    location = "Amsterdam West"
    query = f"airbnb {property_name} {location}"
    google_url = f"https://www.google.com/search?q={quote(query)}"
    
    print(f"--- Testing Google Bypass for: {property_name} ---")
    print(f"1. Simulated Button Click URL: {google_url}")
    
    # Simulate Google Search (Using curl-cffi to avoid bot blocks)
    print("2. Searching Google...")
    session = requests.Session()
    try:
        response = session.get(
            google_url,
            impersonate="chrome120",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        
        # Parse Google Results
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find first Airbnb link
        # Google search results are often in <a> tags with href containing "url?q=" or direct hrefs
        links = soup.find_all('a', href=True)
        found_link = None
        
        for link in links:
            href = link['href']
            if "airbnb.com/rooms" in href or "airbnb.nl/rooms" in href:
                # Clean up Google tracking params if present
                if "/url?q=" in href:
                    href = href.split("/url?q=")[1].split("&")[0]
                found_link = href
                break
        
        if found_link:
            print(f"3. ✅ Success! Google found this Airbnb listing: {found_link}")
            print("   This confirms the 'Via Google' button leads to a valid listing.")
        else:
            print("3. ❌ Could not extract Airbnb link from Google results (might be captchas or layout change).")
            # Fallback check: Did we at least get a 200 OK from Google?
            if response.status_code == 200:
                print("   (Google page loaded successfully, so the user will see results manually)")
            
    except Exception as e:
        print(f"Error fetching Google: {e}")

if __name__ == "__main__":
    verify_google_bypass()
