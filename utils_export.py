import streamlit as st
import pandas as pd
import io
from datetime import datetime

def render_export_buttons(df: pd.DataFrame, prefix_name: str):
    """
    Crée systématiquement deux boutons de téléchargement (CSV et Excel) pour un DataFrame.
    S'utilise de manière transversale dans toutes les vues Ba7ath.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    col_csv, col_xlsx, _ = st.columns([1, 1, 2])
    
    # Export CSV
    try:
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        with col_csv:
            st.download_button(
                label="📥 Exporter en CSV",
                data=csv,
                file_name=f"{prefix_name}_{timestamp}.csv",
                mime="text/csv",
                width="stretch",
                type="primary"
            )
    except Exception as e:
        col_csv.error(f"Erreur CSV : {e}")
        
    # Export Excel
    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Resultats')
        with col_xlsx:
            st.download_button(
                label="📥 Exporter en Excel",
                data=buffer,
                file_name=f"{prefix_name}_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
                type="secondary"
            )
    except Exception as e:
        col_xlsx.error(f"Erreur XLSX : {e}")
