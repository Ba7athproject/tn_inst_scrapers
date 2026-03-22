import requests, urllib3
urllib3.disable_warnings()
from bs4 import BeautifulSoup

url = 'https://www.marchespublics.gov.tn/fr/resultats'
res = requests.get(url, verify=False)
soup = BeautifulSoup(res.text, 'html.parser')

with open("tuneps_analysis.txt", "w", encoding="utf-8") as f:
    f.write('--- FORMS ---\n')
    for frm in soup.find_all('form'):
        f.write(f"Action: {frm.get('action')}\n")
        f.write(f"  Inputs: {[i.get('name') for i in frm.find_all('input')]}\n")
        f.write(f"  Selects: {[s.get('name') for s in frm.find_all('select')]}\n\n")

    f.write('\n--- TABLES ---\n')
    for t in soup.find_all('table'):
        f.write(f"ID: {t.get('id')}, Class: {t.get('class')}\n")
        f.write(f"  Headers: {[th.text.strip() for th in t.find_all('th')]}\n")
        f.write("  Rows sample:\n")
        for i, row in enumerate(t.find_all('tr')[1:4]): # Skip header usually
            f.write(f"    {[td.text.strip() for td in row.find_all('td')]}\n")
        f.write("\n")
