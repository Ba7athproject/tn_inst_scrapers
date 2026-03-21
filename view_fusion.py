import streamlit as st
import pandas as pd

def render_fusion():
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
