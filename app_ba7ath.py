import streamlit as st
import pandas as pd
import time
import requests
import re
import os
import asyncio
import sys
import math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from streamlit_option_menu import option_menu
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ============================================================================
# 🛠️ CORRECTIF SYSTÈME : Installation de Chromium pour Streamlit Cloud
# ============================================================================
os.system("playwright install chromium")

# ============================================================================
# 🛠️ CORRECTIF SYSTÈME : Windows asyncio pour Playwright
# ============================================================================
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ============================================================================
# 🔐 SÉCURITÉ : Couche d'authentification Console
# ============================================================================
def check_password():
    """Vérification du mot de passe via Streamlit Secrets."""
    def password_entered():
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Accès Restreint : ba7ath Institutionnal Scrapers")
        st.text_input("Veuillez saisir le code d'accès investigation :", 
                     type="password", on_change=password_entered, key="password")
        st.info("Cette console est un outil protégé réservé au projet ba7ath.")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Accès Restreint : ba7ath")
        st.text_input("Veuillez saisir le code d'accès investigation :", 
                     type="password", on_change=password_entered, key="password")
        st.error("❌ Code incorrect.")
        return False
    return True

# ============================================================================
# 🛰️ LOGIQUE RNE : RNECore (Moteur d'Investigation API Complet)
# ============================================================================
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

# ============================================================================
# 📜 LOGIQUE JORT : JORTScraper (Navigation Automatisée & Auto-Pagination)
# ============================================================================
class JORTScraper:
    """Moteur de scraping JORT hautement automatisé."""
    def __init__(self, user, pwd, headless=True):
        self.user = user
        self.pwd = pwd
        self.headless = headless
        self.base_url = "https://www.jortsearch.com"

    async def run(self, keyword, max_safety_pages=50):
        async with async_playwright() as p:
            # Masquer la signature du bot
            browser = await p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                # 1. Login avec approche "Clavier Humain" (Contournement Vaadin Shadow DOM)
                await page.goto(f"{self.base_url}/login", wait_until="networkidle", timeout=60000)
                
                user_input = page.locator("input[name='username']")
                await user_input.wait_for(state="visible", timeout=20000)
                
                # Clic explicite puis frappe au clavier système
                await user_input.click()
                await page.keyboard.type(self.user, delay=100)
                
                pass_input = page.locator("input[name='password']")
                await pass_input.click()
                await page.keyboard.type(self.pwd, delay=100)
                
                # Clic sur connexion
                login_btn = page.locator("vaadin-button[theme~='primary']")
                await login_btn.click()
                
                # Attente passive longue pour la création du cookie de session
                await asyncio.sleep(6)
                
                # 2. Recherche (Seulement maintenant qu'on est identifié)
                await page.goto(f"{self.base_url}/search/{keyword}", wait_until="domcontentloaded", timeout=60000)
                
                # --- AUTO-DETECTION DE LA PAGINATION ---
                total_results = 0
                pages_to_scrape = 1
                try:
                    await page.wait_for_selector("announcement-card", timeout=15000)
                    
                    regex_pagination = re.compile(r'\d+\s*-\s*\d+\s+(?:of|sur|de|من)\s+\d+', re.IGNORECASE)
                    pagination_locator = page.locator("span").filter(has_text=regex_pagination).first
                    await pagination_locator.wait_for(timeout=5000)
                    pagination_label = await pagination_locator.inner_text()
                    
                    match_total = re.search(r'\d+\s*-\s*\d+\s+(?:of|sur|de|من)\s+(\d+)', pagination_label, re.IGNORECASE)
                    if match_total:
                        total_results = int(match_total.group(1))
                    
                    total_pages = math.ceil(total_results / 10) if total_results > 0 else 1
                    pages_to_scrape = min(total_pages, max_safety_pages)
                    st.info(f"📊 Compteur détecté : {total_results} annonces. Extraction sur {pages_to_scrape} pages...")
                
                except PlaywrightTimeoutError:
                    # 📸 PREUVE VISUELLE
                    await page.screenshot(path="debug_jort_cloud.png", full_page=True)
                    await browser.close()
                    return pd.DataFrame()
                except Exception:
                    st.info(f"📊 Format de pagination introuvable. Parcours dynamique jusqu'à la limite de {max_safety_pages} pages...")
                    pages_to_scrape = max_safety_pages
                
                all_annonces = []
                for p_idx in range(pages_to_scrape):
                    try:
                        await page.wait_for_selector("announcement-card", timeout=15000)
                        await asyncio.sleep(2) # Stabilisation Vaadin
                    except PlaywrightTimeoutError:
                        break # Fin naturelle (ou page vide)
                    except Exception:
                        break
                        
                    cards = await page.locator("announcement-card").all()
                    if not cards:
                        break
                        
                    for c in cards:
                        try:
                            journal_name = await c.evaluate("node => node.title")
                            categorie_name = await c.evaluate("node => node.subTitle")
                            content_text = await c.locator("span").inner_text()
                            
                            id_match = re.search(r'(\d{4}[A-Z0-9]\d{5}[A-Z]{4}\d)', content_text)
                            
                            all_annonces.append({
                                "Journal": journal_name,
                                "Catégorie": categorie_name,
                                "Contenu": content_text,
                                "ID_JORT": id_match.group(1) if id_match else "N/A",
                                "Extraction": datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                        except: continue
                    
                    # 3. Navigation page suivante dynamique
                    next_btn = page.locator("vaadin-button:has(iron-icon[icon='vaadin:arrow-right'])")
                    if p_idx < pages_to_scrape - 1 and await next_btn.is_visible() and await next_btn.is_enabled():
                        first_card = page.locator("announcement-card").first
                        old_text = await first_card.inner_text()
                        await next_btn.click()
                        
                        try:
                            await page.wait_for_function(
                                """([oldT]) => {
                                    const el = document.querySelector('announcement-card');
                                    return el && el.innerText !== oldT;
                                }""", arg=[old_text], timeout=15000
                            )
                        except: await asyncio.sleep(2)
                    else: 
                        break # Fin naturelle des résultats atteinte
                
                await browser.close()
                return pd.DataFrame(all_annonces)
                
            except Exception as e:
                await browser.close()
                st.error(f"Erreur technique JORT : {e}")
                return pd.DataFrame()

# ============================================================================
# 🖥️ INTERFACE UTILISATEUR : Console ba7ath
# ============================================================================
if check_password():
    st.set_page_config(page_title="ba7ath Console", layout="wide", page_icon="🔍")

    st.markdown("""
        <style>
        .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #00457C; color: white; font-weight: bold; border: none; }
        .stButton>button:hover { background-color: #005fa3; color: white; border: none; }
        [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #d1d5db; }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if os.path.exists("ba7ath.png"):
            st.image("ba7ath.png", width='stretch')
        else:
            st.title("🔍 ba7ath")
        st.divider()
        selected = option_menu(
            menu_title="Navigation",
            options=["RNE", "JORT", "Fusion", "Analyse", "Paramètres"],
            icons=["building", "file-earmark-text", "intersect", "graph-up-arrow", "gear"],
            menu_icon="cast", default_index=0,
            styles={"nav-link-selected": {"background-color": "#00457C"}}
        )

    # --- MODULE RNE ---
    if selected == "RNE":
        st.header("🛰️ Collecte RNE en temps réel")
        col_k, col_t = st.columns([3, 1])
        with col_k: kw = st.text_input("Mot-clé (AR ou FR)", placeholder="ex: الشركة الأهلية", key="rne_kw")
        with col_t: th = st.slider("Puissance (Threads)", 1, 10, 5)

        if st.button("Lancer l'investigation RNE") and kw:
            core = RNECore()
            prog = st.progress(0, text="Initialisation...")
            ids_list, total_target = core.search_ids(kw, prog)
            
            if ids_list:
                st.info(f"Cible : {len(ids_list)} entreprises identifiées.")
                final_data = []
                with st.spinner("Enrichissement exhaustif des fiches..."):
                    with ThreadPoolExecutor(max_workers=th) as executor:
                        futures = [executor.submit(core.fetch_details, e) for e in ids_list]
                        for f in as_completed(futures):
                            res = f.result()
                            if res: final_data.append(res)
                
                if final_data:
                    df = pd.DataFrame(final_data)
                    df.index = list(range(1, len(df) + 1))
                    st.dataframe(df, width='stretch')
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button("📥 Télécharger CSV RNE", data=csv, 
                                     file_name=f"rne_{kw}_{datetime.now().strftime('%Y%m%d')}.csv")
            else: st.warning("Aucun résultat trouvé.")

    # --- MODULE JORT ---
    elif selected == "JORT":
        st.header("📜 Scraping JORT Automatisé")
        col_k, col_p = st.columns([3, 1])
        with col_k: kw_jort = st.text_input("Recherche textuelle JORT", placeholder="ex: International", key="jort_kw")
        with col_p: safety_limit = st.number_input("Limite de sécurité (Pages)", 1, 200, 50)

        if st.button("Lancer l'investigation JORT") and kw_jort:
            if "JORT_USER" not in st.secrets:
                st.error("Secrets JORT_USER / JORT_PASS manquants.")
            else:
                j_scraper = JORTScraper(st.secrets["JORT_USER"], st.secrets["JORT_PASS"], headless=True)
                with st.spinner("Authentification et collecte en cours...") :
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        df_jort = loop.run_until_complete(j_scraper.run(kw_jort, max_safety_pages=safety_limit))
                        loop.close()
                    except Exception as e:
                        st.error(f"Erreur de boucle : {e}")
                        df_jort = pd.DataFrame()
                
                if not df_jort.empty:
                    st.success(f"{len(df_jort)} annonces extraites.")
                    st.dataframe(df_jort, width='stretch')
                    csv_j = df_jort.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button("📥 Télécharger CSV JORT", data=csv_j, file_name=f"jort_{kw_jort}.csv")
                else: 
                    st.warning("Aucune annonce trouvée ou accès bloqué par le serveur.")
                    if os.path.exists("debug_jort_cloud.png"):
                        st.error("🚨 Rapport de débogage (Le serveur est probablement resté bloqué sur la page ci-dessous) :")
                        st.image("debug_jort_cloud.png")

    # --- MODULE FUSION ---
    elif selected == "Fusion":
        st.header("🔀 Fusionneur & Consolidation")
        files = st.file_uploader("Importer les fichiers de collecte", type="csv", accept_multiple_files=True)
        if files and st.button("Générer le Master File"):
            dfs = [pd.read_csv(f) for f in files]
            merged = pd.concat(dfs, ignore_index=True)
            
            # Blindage Fusion (RNE ou JORT)
            if 'ID Unique' in merged.columns:
                master = merged.drop_duplicates(subset=['ID Unique']).copy()
            elif 'ID_JORT' in merged.columns:
                master = merged.drop_duplicates(subset=['ID_JORT']).copy()
            else:
                master = merged.copy()
                
            master.index = list(range(1, len(master) + 1))
            st.success(f"Fusion terminée : {len(master)} entrées uniques.")
            st.dataframe(master, width='stretch')
            st.download_button("📥 Télécharger Master File", master.to_csv(index=False, encoding='utf-8-sig'), "ba7ath_master.csv")

    # --- MODULE ANALYSE ---
    elif selected == "Analyse":
        st.header("📊 Analyse Statistique")
        f_ana = st.file_uploader("Charger un Master File", type="csv")
        if f_ana:
            df_ana = pd.read_csv(f_ana).fillna("Non renseigné")
            c1, c2 = st.columns(2)
            
            with c1:
                # Blindage Analyse 1 (S'adapte aux colonnes RNE ou JORT)
                if 'Ville' in df_ana.columns:
                    st.subheader("Top 10 Villes")
                    st.bar_chart(df_ana[df_ana['Ville'] != "Non renseigné"]['Ville'].value_counts().head(10))
                elif 'Catégorie' in df_ana.columns:
                    st.subheader("Top 10 Catégories JORT")
                    st.bar_chart(df_ana[df_ana['Catégorie'] != "Non renseigné"]['Catégorie'].value_counts().head(10))
                    
            with c2:
                # Blindage Analyse 2 (S'adapte aux colonnes RNE ou JORT)
                if 'Gouvernorat' in df_ana.columns:
                    st.subheader("Distribution Gouvernorats")
                    col_p = 'Gouvernorat' if not df_ana['Gouvernorat'].replace("Non renseigné","").str.strip().eq("").all() else 'Ville'
                    st.bar_chart(df_ana[df_ana[col_p] != "Non renseigné"][col_p].value_counts())
                elif 'Journal' in df_ana.columns:
                    st.subheader("Distribution par Journal")
                    st.bar_chart(df_ana[df_ana['Journal'] != "Non renseigné"]['Journal'].value_counts().head(10))

    # --- MODULE PARAMÈTRES ---
    elif selected == "Paramètres":
        st.header("⚙️ Configuration")
        st.write(f"Utilisateur JORT : `{st.secrets.get('JORT_USER', 'Inconnu')}`")
        st.write(f"OS Plateforme : `{sys.platform}`")
        if st.button("🚪 Déconnexion"):
            del st.session_state["password_correct"]
            st.rerun()

    st.divider()
    st.caption("Console d'investigation ba7ath v9.5 PRO - Standard 2026. (c) Tout droit de reproduction réservé.")