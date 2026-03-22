import requests, urllib3
urllib3.disable_warnings()

url = "https://www.marchespublics.gov.tn/fr/resultats"
headers = {"X-Requested-With": "XMLHttpRequest"}
params = {"draw": "1", "start": "0", "length": "10", "keywords": "logiciel"}

res = requests.get(url, headers=headers, params=params, verify=False)
data = res.json()
print("Keyword test (keywords=logiciel):")
print("Total records:", data.get('recordsTotal'))
print("Filtered records:", data.get('recordsFiltered'))
