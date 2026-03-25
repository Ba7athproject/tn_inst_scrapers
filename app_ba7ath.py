import streamlit as st
import os
from streamlit_option_menu import option_menu

# Imports des modules locaux factorisés
from config import initialize_system
from auth import check_password
from view_rne import render_rne

# Initialisation système (Fix Windows/Playwright)
initialize_system()
from view_fusion import render_fusion
from view_analyse import render_analyse
from view_settings import render_settings
from view_tuneps import render_tuneps
from view_jort import render_jort

# ============================================================================
# 🖥️ POINT D'ENTRÉE STREAMLIT
# ============================================================================
# set_page_config doit être le tout premier appel Streamlit
st.set_page_config(page_title="Ba7ath Tn Scrapers & Intelligence Analytique (Data)", layout="wide", page_icon="🔍")

if check_password():
    # Styles CSS : Branding ba7ath
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

    # Barre Latérale (Navigation)
    with st.sidebar:
        if os.path.exists("ba7ath.png"):
            st.image("ba7ath.png", width='stretch')
        else:
            st.title("🔍 Ba7ath Edge")
        
        st.divider()
        
        # PROMOTION VERSION STANDALONE
        st.info("**Ba7ath Edge Pro (v9.0)**")
        st.link_button("📥 Télécharger l'Application (.exe)", "https://ton-lien-de-telechargement.com", type="primary", use_container_width=True)
        st.caption("Version Windows optimisée (Sans Python).")
        
        st.divider()
        
        selected = option_menu(
            menu_title="Menu d'Investigation",
            options=["RNE", "JORT", "Marchés Publics", "Fusion", "Analyse", "Paramètres"],
            icons=["cloud-download", "journal-bookmark", "briefcase", "intersect", "graph-up-arrow", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "nav-link-selected": {"background-color": "#00457C"},
            }
        )

    # Dispatcher (Routage vers les modules UI)
    if selected == "RNE":
        render_rne()
    elif selected == "JORT":
        render_jort()
    elif selected == "Marchés Publics":
        render_tuneps()
    elif selected == "Fusion":
        render_fusion()
    elif selected == "Analyse":
        render_analyse()
    elif selected == "Paramètres":
        render_settings()

    st.divider()
    st.caption("Console Ba7ath Tn Scrapers & Intelligence Analytique (Data) - Standard de vérification OSINT Tunisie. (c) 2026.")