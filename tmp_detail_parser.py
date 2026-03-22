import requests, urllib3
from bs4 import BeautifulSoup
import json
urllib3.disable_warnings()

url = "https://www.marchespublics.gov.tn/fr/resultats/Award-204387"
res = requests.get(url, verify=False)

if res.status_code == 200:
    soup = BeautifulSoup(res.text, 'html.parser')
    data = {}
    
    # We look for tables or labels
    for row in soup.find_all('tr'):
        label = row.find('th') or row.find('td', class_='label')
        val = row.find('td')
        if label and val and len(row.find_all('td')) >= 1:
            data[label.text.strip()] = val.text.strip()
            
    # Or maybe it's in divs like <div class="label">...</div> <div class="value">...</div>
    for div in soup.find_all('div', class_='row'):
        labels = div.find_all('label')
        for label in labels:
            # Usually the next sibling or parent has the value
            # Let's just grab text
            pass

    print("Extracted fields from detail page:")
    # print some key lines that might contain 'attributaire' or 'montant'
    all_text = soup.get_text(separator='|', strip=True)
    parts = all_text.split('|')
    for i, p in enumerate(parts):
        if 'attribut' in p.lower() or 'fournisseur' in p.lower() or 'montant' in p.lower() or 'société' in p.lower() or 'raison sociale' in p.lower():
            start = max(0, i-2)
            end = min(len(parts), i+3)
            print(f"Match context: {' | '.join(parts[start:end])}")
