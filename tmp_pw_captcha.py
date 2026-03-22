import asyncio
from playwright.async_api import async_playwright

async def test_pw():
    print("Moteur Anti-Bot enclenché...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # On teste headless d'abord pour voir la réaction
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Navigation vers TUNEPS...")
        await page.goto("https://www.marchespublics.gov.tn/fr/resultats")
        html = await page.content()
        
        if "Validation request" in html or "captcha" in html.lower():
            print("🛑 CAPTCHA DÉTECTÉ EN HEADLESS !")
            await browser.close()
            # On relance en Headed pour résolution humaine
            print("🚀 Relance en mode visible pour résolution HUMAINE...")
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://www.marchespublics.gov.tn/fr/resultats")
            
            print("Veuillez résoudre le CAPTCHA dans la fenêtre ouverte...")
            while True:
                html = await page.content()
                if "Validation request" not in html and "captcha" not in html.lower():
                    break
                await asyncio.sleep(1)
            
            print("✅ CAPTCHA RÉSOLU !")
            
        cookies = await context.cookies()
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        ua = await page.evaluate("navigator.userAgent")
        print("COOKIES ACQUIS:")
        print(cookie_string)
        print("UA:", ua)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_pw())
