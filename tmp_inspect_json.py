import requests
import json
import urllib3
urllib3.disable_warnings()

url = "https://www.marchespublics.gov.tn/fr/resultats"
headers = {"X-Requested-With": "XMLHttpRequest"}
params = {"draw": "1", "start": "0", "length": "2"}

res = requests.get(url, headers=headers, params=params, verify=False)
data = res.json()

with open("tuneps_json.txt", "w", encoding="utf-8") as f:
    if 'data' in data and len(data['data']) > 0:
        f.write(json.dumps(data['data'][0], indent=2, ensure_ascii=False))
