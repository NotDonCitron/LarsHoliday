import asyncio
import re
from patchright.async_api import async_playwright
from bs4 import BeautifulSoup

async def debug_airbnb():
    print("Starte Airbnb-Deep-Diagnosis...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        url = "https://www.airbnb.com/s/Zandvoort/homes?checkin=2026-03-15&checkout=2026-03-22"
        print(f"Navigiere zu: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(10)
            await page.mouse.wheel(0, 1500)
            await asyncio.sleep(5)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            cards = soup.find_all('div', {'data-testid': 'card-container'})
            
            print(f"Gefundene Karten: {len(cards)}")
            
            for i, card in enumerate(cards[:3]):
                name_elem = card.find('div', {'data-testid': 'listing-card-title'})
                name = name_elem.get_text(strip=True) if name_elem else "Unknown"
                
                # Check all image tags
                images = card.find_all('img')
                image_urls = [img.get('src', '') for img in images if img.get('src')]
                
                # Check price specifically
                price_text = card.get_text(separator=' ')
                # Find € then a number
                price_match = re.search(r'€\s*(\d+)', price_text)
                
                print(f"--- CARD {i+1} ---")
                print(f"Name: {name}")
                print(f"Price Match: {price_match.group(1) if price_match else 'NONE'}")
                print(f"Images: {len(image_urls)} found")
                for img in image_urls[:2]:
                    print(f"  Img: {img[:60]}...")
                    
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_airbnb())
