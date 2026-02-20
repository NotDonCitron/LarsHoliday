from bs4 import BeautifulSoup
import re

def analyze_booking():
    with open("debug_booking.html", "r") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    cards = soup.find_all('div', {'data-testid': 'property-card'})
    print(f"Gefundene Karten: {len(cards)}")
    
    for i, card in enumerate(cards[:3]):
        print(f"--- ANALYSE KARTE {i+1} ---")
        name_elem = card.find('div', {'data-testid': 'title'}) or card.find('h3')
        name = name_elem.get_text(strip=True) if name_elem else "Unknown"
        print(f"Name: {name}")
        
        # Check image attributes specifically
        img = card.find('img')
        if img:
            print(f"  SRC: {img.get('src', '')[:50]}")
            print(f"  DATA-SRC: {img.get('data-src', '')[:50]}")
            print(f"  SRCSET: {img.get('srcset', '')[:50]}")
        
        # Check price text
        price_elem = card.find('span', {'data-testid': 'price-and-discounted-price'})
        if price_elem:
            print(f"  Price Text: {price_elem.get_text(strip=True)}")

if __name__ == "__main__":
    analyze_booking()
