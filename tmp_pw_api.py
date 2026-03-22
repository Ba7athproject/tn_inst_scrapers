import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        req = context.request
        res = await req.get("https://www.marchespublics.gov.tn/fr/resultats", params={"draw":"1", "start":"0", "length":"10"}, headers={"X-Requested-With": "XMLHttpRequest"})
        text = await res.text()
        print("Playwright APIRequestContext Status:", res.status)
        if "Validation request" in text or "captcha" in text.lower():
            print("❌ Bloqué par CAPTCHA même avec le moteur Chromium !")
        elif text.strip().startswith('{'):
            print("✅ SUCCÈS ! TUNEPS accepte la connexion Headless Chromium sans Cookie !")
        else:
            print("❓ Inconnu:", text[:100])
        await browser.close()
        
if __name__ == "__main__":
    asyncio.run(test())
