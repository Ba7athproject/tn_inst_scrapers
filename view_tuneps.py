import streamlit as st
import pandas as pd
import io
from datetime import datetime
from utils_export import render_export_buttons

def render_tuneps():
    """Rendu de la vue TUNEPS (Marchés Publics) dans Streamlit - Mode HUB uniquement."""
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🏛️ TUNEPS - Hub d'Analyse des Marchés</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Importez vos données extraites via le Scraper Pro (Local) pour analyse.</p>", unsafe_allow_html=True)
    st.markdown("---")

    # --- SECTION 1 : GUIDE D'UTILISATION (Remplacement du Scraping Serveur) ---
    st.markdown("### 🛡️ Guide : Extraction Haute Fidélité (Edge Scraping)")
    
    col_info, col_vocation = st.columns([3, 2])
    with col_info:
        st.info("""
            **Pourquoi le mode local ?**  
            Le site TUNEPS utilise un pare-feu (WAF F5 BIG-IP) qui bloque systématiquement les serveurs cloud. Pour une extraction complète (Parité 100% data), il est nécessaire de lancer le moteur depuis votre propre ordinateur.
        """)
    with col_vocation:
        st.warning("""
            **🔒 Recommandation VPN / Proxy**  
            L'usage d'un VPN (NordVPN, CyberGhost, etc.) est vivement conseillé. Il protège votre IP réelle des bannissements et offre une meilleure stabilité DNS face aux serveurs de TUNEPS.
        """)

    with st.expander("📖 Procédure complète d'extraction (Pas à pas)", expanded=False):
        st.markdown("""
        1. **Téléchargement** : Cliquez sur le bouton ci-dessous pour obtenir l'exécutable portable.
        2. **Préparation** : Activez votre VPN ou Proxy.
        3. **Lancement** : Exécutez `Ba7ath_Scrapers_Pro.exe` sur votre PC Windows.
        4. **Scraping** : Saisissez vos mots-clés et lancez l'extraction. L'outil gère automatiquement les pauses anti-ban.
        5. **Récupération** : Un fichier Excel est généré automatiquement dans le même dossier.
        6. **Importation** : Glissez ce fichier Excel dans la zone ci-dessous.
        """)
    
    # Bouton de Téléchargement (EXE via Github)
    st.link_button(
        "📥 Télécharger Ba7ath_Scrapers_Pro.exe", 
        "https://github.com/Ba7athproject/tn_inst_scrapers/releases/download/v9.0/Ba7ath_Edge_Pro.exe", 
        type="primary",
        help="Télécharge la dernière version stable du moteur de scraping local."
    )

    st.markdown("---")

    # --- SECTION 2 : ZONE D'IMPORTATION & ANALYSE ---
    st.markdown("### 📥 Analyse & Importation des Données")
    
    uploaded_file = st.file_uploader("Glissez-déposez le fichier Excel généré par le Scraper Pro", type=["xlsx"])
    
    if uploaded_file:
        try:
            df_imported = pd.read_excel(uploaded_file)
            st.success(f"✅ {len(df_imported)} marchés chargés. Prêt pour l'analyse RNE.")
            
            col_preview, col_action = st.columns([2, 1])
            with col_action:
                if st.button("🚀 Lancer le Centre d'Intelligence Analytique", type="primary", use_container_width=True):
                    st.session_state['data_to_analyse'] = df_imported
                    st.success("Données envoyées ! Rendez-vous dans l'onglet 'Analyse' pour une exploration globale.")
            
            with col_preview:
                _display_tuneps_results(df_imported, "Import Pro")
                
        except Exception as e:
            st.error(f"Erreur d'importation : {e}")

def _display_tuneps_results(df, search_term):
    """Fonction utilitaire pour afficher les résultats et les boutons d'export."""
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Lien Source": st.column_config.LinkColumn("Fiche TUNEPS", display_text="Ouvrir"),
            "Date de publication": st.column_config.DateColumn("Date")
        }
    )
    
    st.markdown("#### 🔄 Actions & Fusion")
    render_export_buttons(df, f"tuneps_export_{search_term}")

