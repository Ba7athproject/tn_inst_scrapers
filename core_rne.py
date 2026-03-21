import requests
import re
import time
from datetime import datetime

class RNECore:
    """Moteur d'extraction RNE haute performance avec enrichissement complet."""
    BASE_URL_SHORT = "https://www.registre-entreprises.tn/api/rne-api/front-office/shortEntites"
    BASE_URL_DETAILS = "https://www.registre-entreprises.tn/api/rne-api/front-office/entites/short-details"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.registre-entreprises.tn/'
        })

    def _clean(self, val):
        """Nettoyage OSINT : supprime les points inutiles et les valeurs nulles."""
        if val is None or str(val).lower() in ["null", "none", "nan"]:
            return ""
        s = str(val).strip()
        if re.match(r'^\.+$', s): 
            return ""
        return s

    def is_latin(self, text):
        """Détecte la langue pour le paramètre de recherche RNE."""
        return bool(re.search(r'[a-zA-Z]', text))

    def search_ids(self, keyword, progress_bar):
        """Phase 1 : Moissonnage des identifiants avec pagination par curseur AfterID."""
        all_results, seen_ids, last_id, total_prevu = [], set(), "", 0
        is_fr = self.is_latin(keyword)
        param_key = "denominationLatin" if is_fr else "denomination"
        
        while True:
            params = {
                "limit": 10, "afterId": last_id, "typeEntite": "M",
                "notInStatusList": "EN_COURS_CREATION",
                "denomination": "", "denominationLatin": ""
            }
            params[param_key] = keyword

            try:
                resp = self.session.get(self.BASE_URL_SHORT, params=params, timeout=20)
                if resp.status_code != 200: break
                data = resp.json()
                registres = data.get("registres", [])
                if total_prevu == 0: total_prevu = data.get("total", 0)
                if not registres: break
                
                for r in registres:
                    uid = r.get("identifiantUnique")
                    if uid and uid not in seen_ids:
                        seen_ids.add(uid)
                        all_results.append(r)
                
                last_id = registres[-1].get("identifiantUnique")
                prog_val = min(len(all_results) / total_prevu, 1.0) if total_prevu > 0 else 0.5
                progress_bar.progress(prog_val, text=f"Collecte RNE : {len(all_results)} / {total_prevu}")

                if total_prevu > 0 and len(all_results) >= total_prevu: break
                time.sleep(0.3)
            except: break
        return all_results, total_prevu

    def fetch_details(self, entry):
        """Phase 2 : Enrichissement complet avec Adresses, Formes Juridiques et Métadonnées."""
        uid = entry.get("identifiantUnique")
        try:
            url = f"{self.BASE_URL_DETAILS}/{uid}"
            res = self.session.get(url, timeout=15).json()
            
            # Reconstruction précise des adresses
            addr_fr = f"{self._clean(res.get('rueFr'))} {self._clean(res.get('codePostal'))} {self._clean(res.get('villeFr'))}".strip()
            addr_ar = f"{self._clean(res.get('rueAr'))} {self._clean(res.get('codePostal'))} {self._clean(res.get('villeAr'))}".strip()

            return {
                "ID Unique": uid,
                "Dénomination (FR)": self._clean(entry.get("denominationLatin")),
                "Dénomination (AR)": self._clean(res.get("denomination")),
                "Nom Commercial (FR)": self._clean(entry.get("nomCommercialFr")),
                "Nom Commercial (AR)": self._clean(entry.get("nomCommercialAr")),
                "Forme Juridique (FR)": self._clean(res.get("formeJuridiqueFr")),
                "Forme Juridique (AR)": self._clean(res.get("formeJuridiqueAr")),
                "Activité": self._clean(res.get("activiteExerceeFr")),
                "Statut": self._clean(res.get("etatRegistreFr")),
                "Adresse (FR)": addr_fr,
                "Adresse (AR)": addr_ar,
                "Ville": self._clean(res.get("villeFr")),
                "Gouvernorat": self._clean(res.get("bureauRegionalFr")),
                "Extraction (UTC)": datetime.now().isoformat(timespec='seconds'),
                "Source URL": url
            }
        except: return None
