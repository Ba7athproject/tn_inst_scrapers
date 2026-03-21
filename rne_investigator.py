import csv
import time
import requests
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration du logging
logger = logging.getLogger("RNE_Investigation")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)

class RNECursorScraper:
    """
    Scraper RNE avec pagination par curseur et traçabilité métadonnées.
    Optimisé pour la vérification OSINT.
    """
    
    BASE_URL_SHORT = "https://www.registre-entreprises.tn/api/rne-api/front-office/shortEntites"
    BASE_URL_DETAILS = "https://www.registre-entreprises.tn/api/rne-api/front-office/entites/short-details"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.registre-entreprises.tn/search/entite'
        })

    def _clean(self, val):
        return str(val).strip() if val and str(val).lower() != "null" else ""

    def search_all_companies(self, keyword_ar):
        """Récupération exhaustive par afterId."""
        all_results = []
        last_id = "" 
        total_prevu = None
        
        logger.info(f"[*] Début de l'extraction : {keyword_ar}")

        while True:
            params = {
                "limit": 10,
                "afterId": last_id,
                "denomination": keyword_ar,
                "typeEntite": "M",
                "notInStatusList": "EN_COURS_CREATION"
            }

            try:
                resp = self.session.get(self.BASE_URL_SHORT, params=params, timeout=20)
                resp.raise_for_status()
                data = resp.json()
                registres = data.get("registres", [])
                
                if total_prevu is None:
                    total_prevu = data.get("total", 0)
                    logger.info(f"[i] Cible : {total_prevu} entreprises.")

                if not registres: break

                all_results.extend(registres)
                last_id = registres[-1].get("identifiantUnique")
                
                logger.info(f"    > Progression : {len(all_results)}/{total_prevu}")

                if len(all_results) >= total_prevu: break
                time.sleep(0.4)

            except Exception as e:
                logger.error(f"[-] Erreur fetch : {e}")
                break

        return all_results

    def fetch_full_details(self, short_entry):
        """Récupère les détails profonds et injecte les métadonnées de traçabilité."""
        uid = short_entry.get("identifiantUnique")
        try:
            url = f"{self.BASE_URL_DETAILS}/{uid}"
            res = self.session.get(url, timeout=15).json()
            
            # Construction de la fiche enrichie
            return {
                "id_unique": uid,
                "denomination_fr": self._clean(short_entry.get("denominationLatin")),
                "denomination_ar": self._clean(res.get("denomination")),
                "ville": self._clean(res.get("villeFr")),
                "activite": self._clean(res.get("activiteExerceeFr")),
                "statut": self._clean(res.get("etatRegistreFr")),
                # --- BLOC MÉTADONNÉES ---
                "metadata_extracted_at": datetime.now().isoformat(timespec='seconds'),
                "metadata_source_url": url,
                "metadata_api_version": "v1"
            }
        except Exception as e:
            logger.warning(f"[-] Echec ID {uid}: {str(e)}")
            return None

    def run(self, keyword, filename):
        short_list = self.search_all_companies(keyword)
        if not short_list: return

        logger.info(f"[*] Enrichissement et horodatage de {len(short_list)} fiches...")
        final_data = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.fetch_full_details, e) for e in short_list]
            for f in as_completed(futures):
                res = f.result()
                if res: final_data.append(res)

        if final_data:
            # On trie par ID pour garder un fichier propre
            final_data.sort(key=lambda x: x['id_unique'])
            
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=final_data[0].keys())
                writer.writeheader()
                writer.writerows(final_data)
            logger.info(f"[SUCCESS] Extraction terminée : {filename}")

if __name__ == "__main__":
    scraper = RNECursorScraper()
    scraper.run("الشركة الأهلية", "rne_ahliya_traceable.csv")