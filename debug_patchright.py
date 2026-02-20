import asyncio
from patchright.async_api import async_playwright
import sys

async def main():
    print(f"Python: {sys.version}")
    print("Attempting to launch Patchright (Chromium)...")
    try:
        async with async_playwright() as p:
            print("Playwright started.")
            # Try to verify if we can skip dependency validation if needed
            # But usually we just launch
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox'] # often helps in docker/linux
            )
            print("Browser launched successfully!")
            page = await browser.new_page()
            await page.goto("https://example.com")
            print(f"Page title: {await page.title()}")
            await browser.close()
            print("Success!")
    except Exception as e:
        print(f"\nERROR launching browser:\n{e}")

if __name__ == "__main__":
    asyncio.run(main())
