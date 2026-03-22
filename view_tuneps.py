import streamlit as st
import pandas as pd
import io
from datetime import datetime
from core_tuneps import get_tuneps_data
from utils_export import render_export_buttons

def render_tuneps():
    """Rendu de la vue TUNEPS (Marchés Publics) dans Streamlit."""
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🏛️ TUNEPS - Résultats des Appels d'Offres</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Extraction ciblée sur le module des résultats des marchés publics tunisiens.</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Zone de contrôle
    with st.container(border=True):
        st.markdown("#### Filtres de Recherche")
        col1, col2 = st.columns([2, 1])
        with col1:
            tuneps_search = st.text_input(
                "Mots-clés (ex: Logiciel, Nettoyage, etc.)", 
                placeholder="Entrez vos mots-clés de recherche..."
            )
        with col2:
            tuneps_limit = st.selectbox("Nombre max de marchés", [10, 50, 100, 500, 1000], index=1)
            
        with st.expander("Filtres Avancés (Dates, Statuts, PME, Acheteurs)", expanded=False):
            import json, os
            buyers_file = os.path.join(os.path.dirname(__file__), "buyers.json")
            buyers_dict = {"Tous": None}
            if os.path.exists(buyers_file):
                try:
                    with open(buyers_file, "r", encoding="utf-8") as f:
                        buyers_dict.update(json.load(f))
                except Exception:
                    pass
                    
            st.markdown("###### Période de publication")
            col_a, col_b = st.columns(2)
            with col_a:
                date_from = st.date_input("Publié à partir du", value=None)
            with col_b:
                date_to = st.date_input("Publié jusqu'au", value=None)
                
            st.markdown("###### Critères du marché")
            col_c, col_d, col_e = st.columns([2, 1, 1])
            with col_c:
                buyer_ui = st.selectbox("Acheteur Public", list(buyers_dict.keys()))
            with col_d:
                statutOptions = ["Tous", "Attribué", "Infructueux", "Annulé"]
                statut_ui = st.selectbox("Statut du résultat", statutOptions)
            with col_e:
                pmeOptions = ["Tous", "Oui", "Non"]
                pme_ui = st.selectbox("Réservé aux PME", pmeOptions)
                
        # Ligne pour le bouton
        col_btn1, col_btn2, col_btn3 = st.columns([1,2,1])
        with col_btn2:
            st.markdown("<br>", unsafe_allow_html=True)
            search_clicked = st.button("🚀 Lancer l'extraction TUNEPS", width="stretch", type="primary")

    st.markdown("---")

    # Conteneur de résultats
    result_container = st.empty()
    download_container = st.empty()

    if search_clicked:
        if not tuneps_search:
            st.warning("⚠️ Veuillez entrer un mot-clé (ex: JORT, Logiciel...).")
            return

        progress_bar = st.progress(0.0)
        status_text = st.empty()

        # Mapping des statuts et PME
        statut_id = None
        if statut_ui == "Attribué": statut_id = 157
        elif statut_ui == "Infructueux": statut_id = 158
        elif statut_ui == "Annulé": statut_id = 156
        
        sme_id = None
        if pme_ui == "Oui": sme_id = 1
        elif pme_ui == "Non": sme_id = 2
        
        buyer_id = buyers_dict.get(buyer_ui)

        # Lancement du scraper asynchrone
        try:
            df = get_tuneps_data(
                keyword=tuneps_search, 
                date_from=date_from, 
                date_to=date_to, 
                status_id=statut_id, 
                sme_id=sme_id, 
                buyer_id=buyer_id,
                max_results=tuneps_limit
            )
            
            progress_bar.progress(1.0)
            status_text.text("✅ Opération terminée !")
            
            if df.empty:
                result_container.warning("Aucun résultat trouvé pour cette recherche.")
            else:
                st.success(f"Opération réussie : {len(df)} marchés trouvés.")
                st.dataframe(
                    df, 
                    width="stretch", 
                    hide_index=True,
                    column_config={
                        "Lien Source": st.column_config.LinkColumn("Lien Source", display_text="Ouvrir la fiche")
                    }
                )
                
                st.markdown("### 📥 Téléchargements")
                render_export_buttons(df, f"tuneps_export_{tuneps_search}")
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Une erreur critique est survenue : {e}")
