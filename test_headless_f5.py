import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        print("Navigation vers TUNEPS en Firefox Headless...")
        try:
            await page.goto("https://www.marchespublics.gov.tn/fr/resultats", timeout=15000)
            html = await page.content()
            
            if "Validation request" in html or "captcha" in html.lower():
                print("❌ ECHEC : CAPTCHA DETECTE EN HEADLESS.")
            else:
                print("✅ SUCCES : TUNEPS ACCESSIBLE EN HEADLESS SANS CAPTCHA !")
                
        except Exception as e:
            print(f"Erreur: {e}")
        await browser.close()
asyncio.run(main())
