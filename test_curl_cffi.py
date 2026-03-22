import asyncio
from curl_cffi.requests import AsyncSession

async def main():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    print("Envoi de la requête via curl_cffi avec usurpation TLS Chrome120...")
    try:
        # On utilise une session pour sauvegarder les cookies
        async with AsyncSession(impersonate="chrome120", verify=False) as session:
            # Requete initiale pour obtenir les cookies WAF si besoin
            res = await session.get("https://www.marchespublics.gov.tn/fr/resultats", headers=headers, timeout=15)
            html = res.text
            
            if "Validation request" in html or "captcha" in html.lower():
                print("❌ ECHEC : CAPTCHA F5 (JS/Fingerprint avancé requis).")
                print("Extrait:", html[:250])
            else:
                print("✅ SUCCES : TUNEPS ACCESSIBLE avec curl_cffi SEC sans captcha !")
                
            # Test API
            api_headers = headers.copy()
            api_headers['X-Requested-With'] = 'XMLHttpRequest'
            api_headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
            res_api = await session.get("https://www.marchespublics.gov.tn/fr/resultats?draw=1&start=0&length=10&keywords=jort", headers=api_headers)
            
            try:
                data = res_api.json()
                print(f"✅ SUCCES API : Trouvé {data.get('recordsFiltered', 0)} résultats.")
            except:
                print("❌ ECHEC API : Pas de JSON valide retourné.", res_api.text[:200])

    except Exception as e:
        print(f"Erreur réseau: {e}")

asyncio.run(main())
