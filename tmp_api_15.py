import requests, json, urllib3
urllib3.disable_warnings()

res = requests.get('https://www.marchespublics.gov.tn/fr/resultats', headers={'X-Requested-With': 'XMLHttpRequest'}, params={'draw': '1', 'start': '0', 'length': '15'}, verify=False)
with open('tuneps_15_rows.json', 'w', encoding='utf-8') as f:
    json.dump(res.json(), f, ensure_ascii=False, indent=2)
