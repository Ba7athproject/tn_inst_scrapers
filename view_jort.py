import streamlit as st
import pandas as pd
import asyncio
import os
import json
from core_jort import JORTScraper

def render_jort():
    st.header("⚖️ Collecte Journal Officiel (JORT)")
    
    st.info("""
        **Autonomie Totale** : L'application "Ba7ath EDGE Pro v9.0" gère désormais le scraping JORT en local (via Playwright). 
        Cela garantit une indépendance complète aux enquêteurs dans leurs recherches d'annonces légales.
    """)
    
    st.markdown("Extraction des annonces légales via **jortsearch.com**.")
    
    col_k, col_p, col_y1, col_y2 = st.columns([3, 1, 1, 1])
    with col_k:
        keyword = st.text_input("Référence ou Mot-clé JORT", placeholder="ex: STEG, Fonds de commerce...", key="input_jort")
    with col_p:
        max_pages = st.number_input("Pages/an", min_value=1, max_value=100, value=5)
    with col_y1:
        year_start = st.number_input("An début", min_value=2000, max_value=2026, value=2023)
    with col_y2:
        year_end = st.number_input("An fin", min_value=2000, max_value=2026, value=2025)

    if st.button("Démarrer le Scraping JORT") and keyword:
        # Récupération des credentials (priorité : session_state > jort_credentials.json > st.secrets)
        user = st.session_state.get("jort_user")
        pwd = st.session_state.get("jort_pass")

        if not user or not pwd:
            cred_path = "jort_credentials.json"
            if os.path.exists(cred_path):
                try:
                    with open(cred_path, "r") as f:
                        creds = json.load(f)
                        user = creds.get("user")
                        pwd = creds.get("pass")
                except: pass
        
        if not user or not pwd:
            user = st.secrets.get("JORT_USER")
            pwd = st.secrets.get("JORT_PASS")
        
        if not user or not pwd:
            st.error("⚠️ Identifiants JORT manquants. Veuillez les renseigner dans l'onglet **Paramètres**.")
            return

        scraper = JORTScraper(user, pwd, headless=True)
        
        with st.spinner("Initialisation du navigateur JORT..."):
            # Exécution asynchrone dans Streamlit
            try:
                # Utilisation de asyncio directement puisque Streamlit tourne déjà dans un loop ou thread
                # Mais il faut être prudent avec les event loops.
                # Une approche sûre est d'utiliser loop.run_until_complete si possible, 
                # ou simplement await si on est dans un contexte asynchrone.
                # Streamlit asynchrone (versions récentes) supporte l'affichage direct.
                
                async def run_and_display():
                    df = await scraper.run(keyword, max_safety_pages=max_pages, year_range=(year_start, year_end))
                    return df
                
                # Pour les versions de Streamlit qui supportent l'async dans les callbacks (si applicable)
                # Sinon on utilise une astuce de boucle d'événement.
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                df_jort = loop.run_until_complete(run_and_display())
                
                if not df_jort.empty:
                    st.success(f"Extraction terminée : {len(df_jort)} annonces trouvées.")
                    st.dataframe(df_jort, width='stretch')
                    from utils_export import render_export_buttons
                    st.markdown("### 📥 Téléchargements")
                    render_export_buttons(df_jort, f"jort_export_{keyword}")
                else:
                    st.warning("Aucune annonce trouvée ou erreur de connexion.")
                    
            except Exception as e:
                st.error(f"Erreur lors de l'exécution : {e}")
