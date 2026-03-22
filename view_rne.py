import streamlit as st
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from core_rne import RNECore

def render_rne():
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
                from utils_export import render_export_buttons
                st.markdown("### 📥 Téléchargements")
                render_export_buttons(df, f"rne_export_{keyword}")
        else:
            st.warning("Aucun résultat trouvé.")
