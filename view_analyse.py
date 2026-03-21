import streamlit as st
import pandas as pd

def render_analyse():
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
                data_villes = df_ana[df_ana['Ville'] != "Non renseigné"]['Ville'].value_counts().head(10)
                st.bar_chart(data_villes)
        
        with c2:
            st.subheader("Répartition par Statut")
            if 'Statut' in df_ana.columns:
                st.write(df_ana['Statut'].value_counts())
        
        st.divider()
        st.subheader("Distribution Géographique")
        col_plot = 'Gouvernorat'
        if 'Gouvernorat' in df_ana.columns:
            if df_ana['Gouvernorat'].replace("Non renseigné", "").str.strip().eq("").all():
                st.warning("Champ 'Gouvernorat' vide. Affichage par défaut via les données de Ville.")
                col_plot = 'Ville'
            
            if col_plot in df_ana.columns:
                counts = df_ana[df_ana[col_plot] != "Non renseigné"][col_plot].value_counts()
                st.bar_chart(counts)
