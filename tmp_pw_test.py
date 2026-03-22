from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    page = context.new_page()
    res = page.goto("https://www.marchespublics.gov.tn/fr/resultats")
    print("HTTP Status:", res.status)
    content = page.content()
    if "Validation request" in content or "captcha" in content.lower():
        print("[-] Playwright a aussi reçu le CAPTCHA.")
    else:
        print("[+] Playwright a CONTOURNÉ le CAPTCHA !")
        
    api_res = page.evaluate('''async () => {
        let r = await fetch("/fr/resultats?draw=1&start=0&length=10", {
            headers: {"X-Requested-With": "XMLHttpRequest"}
        });
        return await r.text();
    }''')
    print("JSON valide ?", api_res.strip().startswith('{'))
    browser.close()
