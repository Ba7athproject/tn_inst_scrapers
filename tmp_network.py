import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Listening to network responses...")
        
        async def handle_response(response):
            # We want to catch JSON responses or large HTML chunks
            if "application/json" in response.headers.get("content-type", "") or "text/html" in response.headers.get("content-type", ""):
                if "resultats" in response.url or "ajax" in response.url or "api" in response.url:
                    print(f"URL: {response.url}")
                    print(f"Status: {response.status}")
                    
        page.on("response", handle_response)
        
        print("Navigating...")
        await page.goto("https://www.marchespublics.gov.tn/fr/resultats", wait_until="networkidle")
        
        await asyncio.sleep(2) # let any ajax finish
        await browser.close()

asyncio.run(main())
