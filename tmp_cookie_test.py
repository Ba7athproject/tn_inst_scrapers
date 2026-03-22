import requests
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
# 1. Visiter la page normale pour acquérir les cookies
res1 = s.get('https://www.marchespublics.gov.tn/fr/resultats', verify=False)
print("[+] Cookies acquis:", s.cookies.get_dict())

# 2. Lancer la requête API JSON avec les cookies
res2 = s.get('https://www.marchespublics.gov.tn/fr/resultats', 
             params={'draw': '1', 'start': '0', 'length': '10', 'keywords': 'logiciels'}, 
             headers={'X-Requested-With': 'XMLHttpRequest'}, 
             verify=False)

print("[+] Status API:", res2.status_code)
print("[+] Est-ce un JSON valide ?", res2.text.strip().startswith('{'))
if not res2.text.strip().startswith('{'):
    print(res2.text[:200])
