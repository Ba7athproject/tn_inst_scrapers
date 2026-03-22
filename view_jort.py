import streamlit as st
import pandas as pd
import asyncio
from core_jort import JORTScraper

def render_jort():
    st.header("⚖️ Collecte Journal Officiel (JORT)")
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
        # Récupération des credentials
        user = st.secrets.get("JORT_USER")
        pwd = st.secrets.get("JORT_PASS")
        
        if not user or not pwd:
            st.error("Identifiants JORT manquants dans les secrets.")
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
