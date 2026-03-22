import streamlit as st
import pandas as pd
from utils_export import render_export_buttons

def render_fusion():
    st.header("🔀 Fusionneur & Consolidation")
    st.markdown("Combinez plusieurs extractions pour générer votre **Master File** parfait.")
    
    files = st.file_uploader("Importer les fichiers (CSV ou Excel)", type=["csv", "xlsx"], accept_multiple_files=True)
    
    if files:
        dfs = []
        for f in files:
            try:
                if f.name.endswith('.csv'):
                    d = pd.read_csv(f)
                else:
                    d = pd.read_excel(f)
                dfs.append(d)
            except Exception as e:
                st.error(f"Impossible de lire le fichier {f.name} : {e}")
        
        if dfs:
            # Identification des colonnes communes pour déduplication potentielle
            colonnes_communes = list(set.intersection(*(set(df.columns) for df in dfs)))
            
            st.markdown("### Paramètres de fusion")
            if colonnes_communes:
                dedup_col = st.selectbox(
                    "Sélectionnez le pivot de déduplication (Optionnel)", 
                    ["Ne pas dédupliquer"] + sorted(colonnes_communes),
                    help="Si vous fusionnez des fichiers RNE, choisissez 'Numéro RNE'. Pour TUNEPS, choisissez 'Lien Source'."
                )
            else:
                st.warning("⚠️ Aucune colonne commune détectée pour dédupliquer de façon croisée.")
                dedup_col = "Ne pas dédupliquer"
                
            if st.button("🚀 Lancer la Fusion Stratégique", type="primary"):
                merged = pd.concat(dfs, ignore_index=True)
                
                if dedup_col != "Ne pas dédupliquer" and dedup_col in merged.columns:
                    master = merged.drop_duplicates(subset=[dedup_col]).copy()
                    st.success(f"Opération réussie : {len(merged)} lignes brutes consolidées en {len(master)} entités uniques.")
                else:
                    master = merged.copy()
                    st.success(f"Opération réussie (Superposition simple) : {len(master)} lignes intégrées.")
                
                # Réinitialisation de l'index pour propreté
                master.index = list(range(1, len(master) + 1))
                
                st.dataframe(master, width='stretch')
                
                st.markdown("### Exportation")
                render_export_buttons(master, "ba7ath_master")
