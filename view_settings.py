import streamlit as st
import sys

def render_settings():
    st.header("⚙️ Paramètres Console")
    st.write("**Projet :** ba7ath - Investigation RNE")
    st.write("**Version :** 6.5 (Auth + Fixed Analytics)")
    st.divider()
    if st.button("🚪 Déconnexion (Logout)"):
        del st.session_state["password_correct"]
        st.rerun()
