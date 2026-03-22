import aiohttp
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import ssl
import random

class TunepsScraper:
    def __init__(self):
        self.base_url = "https://www.marchespublics.gov.tn/fr/resultats"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.marchespublics.gov.tn',
            'Referer': 'https://www.marchespublics.gov.tn/fr/resultats',
            'Connection': 'keep-alive',
        }
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Le proxy peut être configuré dans Streamlit via le fichier secrets.toml
        # ou via les variables d'environnement du serveur (utile pour DigitalOcean/Render/AWS).
        from typing import Optional
        self.proxy_url: Optional[str] = None
        import os
        try:
            if "TUNEPS_PROXY" in st.secrets:
                self.proxy_url = st.secrets["TUNEPS_PROXY"]
            elif os.getenv("TUNEPS_PROXY"):
                self.proxy_url = os.getenv("TUNEPS_PROXY")
        except Exception:
            self.proxy_url = os.getenv("TUNEPS_PROXY")

    async def _fetch_detail_page(self, session, award_id):
        """Récupère les détails spécifiques du marché pour enrichir la donnée."""
        url = f"https://www.marchespublics.gov.tn/fr/resultats/{award_id}"
        details = {
            "Montant HT": "",
            "Montant TTC": "",
            "Personnalité juridique": "",
            "PME": "",
            "Nationalité": "",
            "RNE": "",
            "Région": "",
            "Attributaire (Gagnant)": ""
        }
        
        headers_html = self.headers.copy()
        headers_html['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
        headers_html.pop('X-Requested-With', None)
        
        try:
            async with session.get(url, headers=headers_html, proxy=self.proxy_url, ssl=self.ssl_context) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    for row in soup.find_all('tr'):
                        cells = row.find_all(['th', 'td'])
                        if len(cells) == 2:
                            key = cells[0].text.strip()
                            val = cells[1].text.strip()
                            if key in details:
                                details[key] = val
                            elif key == "Raison sociale fr":
                                details["Attributaire (Gagnant)"] = val
                        elif len(cells) == 4:
                            key1 = cells[0].text.strip()
                            if key1 in details:
                                details[key1] = cells[1].text.strip()
                            elif key1 == "Raison sociale fr":
                                details["Attributaire (Gagnant)"] = cells[1].text.strip()
                                
                            key2 = cells[2].text.strip()
                            if key2 in details:
                                details[key2] = cells[3].text.strip()
                            elif key2 == "Raison sociale fr":
                                details["Attributaire (Gagnant)"] = cells[3].text.strip()

        except Exception:
            pass # Silencieux pour ne pas interrompre l'extraction globale en cas de problème sur une seule fiche
        return details

    async def run(self, keyword: str, date_from=None, date_to=None, status_id=None, sme_id=None, buyer_id=None, max_results=50):
        # Utiliser st.empty() géré dans view_tuneps si dispo, sinon ignorons
        try:
            status_text = st.session_state.get('_tuneps_status_placeholder')
            progress_bar = st.session_state.get('_tuneps_progress_placeholder')
        except:
            status_text, progress_bar = None, None

        params = {
            'draw': '1',
            'start': '0',
            'length': str(max_results),
            'keywords': keyword,
        }
        
        if date_from:
            params['publication_date_from'] = date_from.strftime('%d/%m/%Y')
        if date_to:
            params['publication_date_to'] = date_to.strftime('%d/%m/%Y')
        if status_id:
            params['award_category'] = str(status_id)
        if sme_id:
            params['sme'] = str(sme_id)
        if buyer_id:
            params['organization'] = str(buyer_id)

        results = []
        
        try:
            timeout = aiohttp.ClientTimeout(total=45)
            # IMPORTANT: Limite stricte des connexions pour ne pas déclencher l'anti-DDoS WAF
            connector = aiohttp.TCPConnector(limit=5, ssl=self.ssl_context)
            
            # trust_env=True permet aussi à aiohttp d'utiliser nativement HTTP_PROXY s'il est configuré sur l'OS du serveur
            async with aiohttp.ClientSession(connector=connector, timeout=timeout, trust_env=True) as session:
                
                # 1. Requête principale JSON (liste des appels d'offres)
                async with session.get(self.base_url, headers=self.headers, params=params, proxy=self.proxy_url) as response:
                    if response.status != 200:
                        raise Exception(f"Erreur HTTP API ({response.status}). Le serveur TUNEPS WAF bloque la requête. Veuillez attendre quelques minutes.")
                    
                    try:
                        data = await response.json(content_type=None)
                    except Exception:
                        text = await response.text()
                        if "Validation request" in text or "captcha" in text.lower() or "f5" in text.lower():
                            raise Exception("🛑 BLOCAGE ANTI-BOT (CAPTCHA) ACTIVÉ. Votre IP a été bloquée temporairement par TUNEPS suite à un nombre important de requêtes passées. La solution : Ouvrez www.marchespublics.gov.tn dans votre navigateur Web classique, passez le Captcha, et revenez relancer ici.")
                        raise Exception(f"Format inattendu reçu : {text[:100]}")
                        
                    records = data.get('data', [])
                    
                    if not records:
                        return pd.DataFrame()
                    
                    records = records[:max_results]
                    
                # 2. Enrichissement des fiches de détail avec Limiteur de Vitesse pour Anti-DDoS
                # Utilisation d'un sémaphore de 2 requêtes concurrentes maximum (le WAF de TUNEPS bloque à 5+)
                sem = asyncio.Semaphore(2)
                
                async def fetch_with_throttle(aw_id):
                    async with sem:
                        # Délai aléatoire entre chaque requête pour imiter un humain et éviter le bannissement F5
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                        return await self._fetch_detail_page(session, aw_id)
                        
                tasks = []
                for record in records:
                    award_id = record.get('id', '')
                    tasks.append(fetch_with_throttle(award_id))
                
                # Exécution contrôlée
                details = await asyncio.gather(*tasks)
                
                # 3. Assemblage des données final
                for i, record in enumerate(records):
                    lot = record.get('lot', {})
                    tender = lot.get('tender', {})
                    org = tender.get('organization', {})
                    
                    acheteur = org.get('name_fr', 'Indisponible')
                    objet = tender.get('title_fr', tender.get('title_ar', 'Indisponible'))
                    date_pub = record.get('publication_date', 'Inconnue')
                    award_id = record.get('id', '')
                    cat_id = str(record.get('award_category', ''))
                    cat_label = "Attribué" if cat_id == "157" else "Infructueux" if cat_id == "158" else "Annulé" if cat_id == "156" else "Inconnu"
                    
                    det = details[i]
                    
                    results.append({
                        "Date de publication": date_pub,
                        "Objet de l'appel d'offres": objet,
                        "Acheteur Public": acheteur,
                        "Catégorie de résultat": cat_label,
                        "Attributaire (Gagnant)": det.get("Attributaire (Gagnant)", ""),
                        "Personnalité juridique": det.get("Personnalité juridique", ""),
                        "Nationalité": det.get("Nationalité", ""),
                        "RNE": det.get("RNE", ""),
                        "PME": det.get("PME", ""),
                        "Région": det.get("Région", ""),
                        "Montant HT": det.get("Montant HT", ""),
                        "Montant TTC": det.get("Montant TTC", ""),
                        "Lien Source": f"https://www.marchespublics.gov.tn/fr/resultats/{award_id}"
                    })
                            
        except Exception as e:
            st.error(f"❌ Erreur lors du scraping TUNEPS : {e}")
            return pd.DataFrame()
            
        return pd.DataFrame(results)

def get_tuneps_data(keyword: str, date_from=None, date_to=None, status_id=None, sme_id=None, buyer_id=None, max_results=50):
    scraper = TunepsScraper()
    return asyncio.run(scraper.run(
        keyword, 
        date_from=date_from, 
        date_to=date_to, 
        status_id=status_id, 
        sme_id=sme_id, 
        buyer_id=buyer_id,
        max_results=max_results
    ))
