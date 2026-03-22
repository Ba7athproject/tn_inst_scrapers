import requests, urllib3
urllib3.disable_warnings()
from bs4 import BeautifulSoup

url = 'https://www.marchespublics.gov.tn/fr/resultats'
res = requests.get(url, verify=False)
soup = BeautifulSoup(res.text, 'html.parser')

print('--- FORMS ---')
for f in soup.find_all('form'):
    print(f"Action: {f.get('action')}")
    print(f"  Inputs: {[i.get('name') for i in f.find_all('input')]}")
    print(f"  Selects: {[s.get('name') for s in f.find_all('select')]}")

print('\n--- TABLES ---')
for t in soup.find_all('table'):
    print(f"ID: {t.get('id')}, Class: {t.get('class')}")
    print(f"  Headers: {[th.text.strip() for th in t.find_all('th')]}")
