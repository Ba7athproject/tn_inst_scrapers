import requests, json, urllib3
urllib3.disable_warnings()

url = "https://www.marchespublics.gov.tn/fr/resultats"
headers = {"X-Requested-With": "XMLHttpRequest"}
# Test a keyword that should have fewer matches
params = {"draw": "1", "start": "0", "length": "10", "search[value]": "logiciel"}

res = requests.get(url, headers=headers, params=params, verify=False)
data = res.json()
print("Keyword: logiciel")
print("Total records:", data.get('recordsTotal'))
print("Filtered records:", data.get('recordsFiltered'))
if data.get('recordsFiltered', 0) > 0 and len(data.get('data', [])) > 0:
    print("First match:", data['data'][0]['lot']['tender']['title_fr'])
