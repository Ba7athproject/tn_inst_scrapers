import requests
from bs4 import BeautifulSoup
import json
import urllib3
urllib3.disable_warnings()

res = requests.get('https://www.marchespublics.gov.tn/fr/resultats/Award-204387', verify=False)
soup = BeautifulSoup(res.text, 'html.parser')

data = {}
for row in soup.find_all('tr'):
    cells = row.find_all(['th', 'td'])
    if len(cells) == 2:
        key = cells[0].text.strip()
        val = cells[1].text.strip()
        if key: data[key] = val
    elif len(cells) == 4:
        key1 = cells[0].text.strip()
        if key1: data[key1] = cells[1].text.strip()
        key2 = cells[2].text.strip()
        if key2: data[key2] = cells[3].text.strip()

with open('detail_output.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
