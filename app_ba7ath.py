import streamlit as st
import pandas as pd
import time
import requests
import re
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from streamlit_option_menu import option_menu

# ============================================================================
# SÉCURITÉ : Couche d'authentification
# ============================================================================
def check_password():
    """Retourne True si l'utilisateur a saisi le bon mot de passe."""
    def password_entered():
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Sécurité : on supprime le texte clair
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Affichage initial du formulaire de login
        st.title("🔐 Accès Restreint : ba7ath")
        st.text_input("Saisissez le code d'accès investigation :", 
                     type="password", on_change=password_entered, key="password")
        st.info("Cette console est un outil protégé du projet ba7ath.")
        return False
    elif not st.session_state["password_correct"]:
        # Erreur de mot de passe
        st.title("🔐 Accès Restreint : ba7ath")
        st.text_input("Saisissez le code d'accès investigation :", 
                     type="password", on_change=password_entered, key="password")
        st.error("❌ Code incorrect.")
        return False
    else:
        return True

# ============================================================================
# LOGIQUE TECHNIQUE : RNECore (Moteur d'Extraction)
# ============================================================================
class RNECore:
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
        if re.match(r'^\.+$', s): # Supprime les pollutions de type "..."
            return ""
        return s

    def is_latin(self, text):
        return bool(re.search(r'[a-zA-Z]', text))

    def search_ids(self, keyword, progress_bar):
        """Moissonnage des IDs avec pagination par curseur."""
        all_results = []
        seen_ids = set()
        last_id = ""
        total_prevu = 0
        
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
                
                # Barre de progression calculée sur le total réel
                prog_val = min(len(all_results) / total_prevu, 1.0) if total_prevu > 0 else 0.5
                progress_bar.progress(prog_val, text=f"Collecte : {len(all_results)} / {total_prevu}")

                if total_prevu > 0 and len(all_results) >= total_prevu: break
                time.sleep(0.3)
            except: break
            
        return all_results, total_prevu

    def fetch_details(self, entry):
        """Enrichissement complet avec Adresses, Formes Juridiques et Métadonnées."""
        uid = entry.get("identifiantUnique")
        try:
            url = f"{self.BASE_URL_DETAILS}/{uid}"
            res = self.session.get(url, timeout=15).json()
            
            # Reconstruction des adresses
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

# ============================================================================
# INTERFACE UTILISATEUR (Streamlit 2026 Ready)
# ============================================================================
if check_password():
    st.set_page_config(page_title="ba7ath RNE Console", layout="wide", page_icon="🔍")

    # Injection CSS : Branding ba7ath
    st.markdown("""
        <style>
        .stButton>button { 
            width: 100%; border-radius: 8px; height: 3.5em; 
            background-color: #00457C; color: white; font-weight: bold; border: none;
        }
        .stButton>button:hover { background-color: #005fa3; color: white; border: none; }
        [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #d1d5db; }
        </style>
    """, unsafe_allow_html=True)

    # Barre Latérale (Navigation à gauche)
    with st.sidebar:
        if os.path.exists("ba7ath.png"):
            st.image("ba7ath.png", width='stretch')
        else:
            st.title("🔍 ba7ath")
        
        st.divider()
        
        selected = option_menu(
            menu_title="Menu d'Investigation",
            options=["Collecte", "Fusion", "Analyse", "Paramètres"],
            icons=["cloud-download", "intersect", "graph-up-arrow", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "nav-link-selected": {"background-color": "#00457C"},
            }
        )

    # --- MODULE 1 : COLLECTE ---
    if selected == "Collecte":
        st.header("🛰️ Collecte RNE en temps réel")
        col_k, col_t = st.columns([3, 1])
        with col_k:
            keyword = st.text_input("Mot-clé (AR ou FR)", placeholder="ex: الشركة العالمية", key="input_keyword")
        with col_t:
            threads = st.slider("Puissance (Threads)", 1, 10, 5)

        if st.button("Lancer l'investigation") and keyword:
            scraper = RNECore()
            prog = st.progress(0, text="Connexion au registre...")
            ids_list, total_target = scraper.search_ids(keyword, prog)
            
            if ids_list:
                st.info(f"Cible : {len(ids_list)} entreprises identifiées.")
                final_data = []
                with st.spinner("Enrichissement des fiches détaillées..."):
                    with ThreadPoolExecutor(max_workers=threads) as executor:
                        futures = [executor.submit(scraper.fetch_details, e) for e in ids_list]
                        for f in as_completed(futures):
                            res = f.result()
                            if res: final_data.append(res)
                
                if final_data:
                    df = pd.DataFrame(final_data)
                    df.index = list(range(1, len(df) + 1))
                    st.dataframe(df, width='stretch')
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button("📥 Télécharger le CSV", data=csv, 
                                     file_name=f"rne_{keyword}_{datetime.now().strftime('%Y%m%d')}.csv")
            else:
                st.warning("Aucun résultat trouvé.")

    # --- MODULE 2 : FUSION ---
    elif selected == "Fusion":
        st.header("🔀 Fusionneur & Consolidation")
        st.markdown("Combinez plusieurs fichiers pour générer votre **Master File** sans doublons d'ID.")
        
        files = st.file_uploader("Importer les fichiers CSV", type="csv", accept_multiple_files=True)
        
        if files:
            if st.button("Lancer la Fusion"):
                dfs = []
                for f in files:
                    d = pd.read_csv(f).rename(columns={'Metadata: Extrait le': 'Extraction (UTC)', 'Metadata: Source': 'Source URL'})
                    dfs.append(d)
                
                if dfs:
                    merged = pd.concat(dfs, ignore_index=True)
                    if 'ID Unique' in merged.columns:
                        master = merged.drop_duplicates(subset=['ID Unique']).copy()
                        master.index = list(range(1, len(master) + 1))
                        st.success(f"Fusion terminée : {len(merged)} lignes ➔ {len(master)} entreprises uniques.")
                        st.dataframe(master, width='stretch')
                        csv_m = master.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button("📥 Télécharger le Master File", data=csv_m, file_name="ba7ath_master_file.csv")

    # --- MODULE 3 : ANALYSE ---
    elif selected == "Analyse":
        st.header("📊 Analyse statistique")
        file_ana = st.file_uploader("Charger un fichier CSV pour analyse", type="csv")
        
        if file_ana:
            df_ana = pd.read_csv(file_ana).fillna("Non renseigné")
            df_ana.replace("", "Non renseigné", inplace=True)
            
            st.divider()
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("Top 10 Villes")
                if 'Ville' in df_ana.columns:
                    # On retire "Non renseigné" pour ne pas polluer le graphique
                    data_villes = df_ana[df_ana['Ville'] != "Non renseigné"]['Ville'].value_counts().head(10)
                    st.bar_chart(data_villes)
            
            with c2:
                st.subheader("Répartition par Statut")
                if 'Statut' in df_ana.columns:
                    st.write(df_ana['Statut'].value_counts())
            
            st.divider()
            st.subheader("Distribution Géographique")
            # Logique Fallback : Si Gouvernorat est vide, on prend la Ville
            col_plot = 'Gouvernorat'
            if df_ana['Gouvernorat'].replace("Non renseigné", "").str.strip().eq("").all():
                st.warning("Champ 'Gouvernorat' vide. Affichage par défaut via les données de Ville.")
                col_plot = 'Ville'
            
            counts = df_ana[df_ana[col_plot] != "Non renseigné"][col_plot].value_counts()
            st.bar_chart(counts)

    # --- MODULE 4 : PARAMÈTRES ---
    elif selected == "Paramètres":
        st.header("⚙️ Paramètres Console")
        st.write("**Projet :** ba7ath - Investigation RNE")
        st.write("**Version :** 6.5 (Auth + Fixed Analytics)")
        st.divider()
        if st.button("🚪 Déconnexion (Logout)"):
            del st.session_state["password_correct"]
            st.rerun()

    st.divider()
    st.caption("Console ba7ath - Standard de vérification OSINT Tunisie. (c) 2026.")