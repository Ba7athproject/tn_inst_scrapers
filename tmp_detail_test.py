import requests, urllib3
from bs4 import BeautifulSoup
urllib3.disable_warnings()

award_id = "Award-204387"
urls_to_test = [
    f"https://www.marchespublics.gov.tn/fr/resultats/{award_id}",
    f"https://www.marchespublics.gov.tn/fr/award/{award_id}",
    f"https://www.marchespublics.gov.tn/fr/public/award/{award_id}",
    f"https://www.marchespublics.gov.tn/fr/public/resultats/{award_id}"
]

for url in urls_to_test:
    res = requests.get(url, verify=False)
    print(f"URL: {url} -> Status: {res.status_code}")
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        # Check if the page looks like a detail page by searching for "Attributaire" or "Montant"
        text = soup.get_text().lower()
        if "attributaire" in text or "fournisseur" in text or "montant" in text:
            print("  [SUCCESS] Detail page found!")
            print("  Title:", soup.title.string if soup.title else "No title")
            # Extract a snippet to verify
            print("  Snippet:", text[text.find("attributaire")-20:text.find("attributaire")+100].replace('\n', ' '))
            break
