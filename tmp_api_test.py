import requests, urllib3
urllib3.disable_warnings()

url = "https://www.marchespublics.gov.tn/fr/resultats"
headers = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
params = {
    "draw": "1",
    "start": "0",
    "length": "10",
    "search[value]": ""
}

res = requests.get(url, headers=headers, params=params, verify=False)
try:
    data = res.json()
    print("Success! JSON keys:", data.keys())
    print("Records Total:", data.get('recordsTotal'))
    if 'data' in data and len(data['data']) > 0:
        print("First row Sample:", data['data'][0])
except Exception as e:
    print("Failed to parse JSON:", res.text[:200])
