import streamlit as st

def check_password():
    """Vérification du mot de passe via Streamlit Secrets."""
    def password_entered():
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Accès Restreint : ba7ath")
        st.text_input("Veuillez saisir le code d'accès investigation :", 
                     type="password", on_change=password_entered, key="password")
        st.info("Cette console est un outil protégé réservé au projet ba7ath.")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Accès Restreint : ba7ath")
        st.text_input("Veuillez saisir le code d'accès investigation :", 
                     type="password", on_change=password_entered, key="password")
        st.error("❌ Code incorrect.")
        return False
    return True
