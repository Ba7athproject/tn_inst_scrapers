import streamlit as st
import os

def check_password():
    """Vérification du mot de passe avec une interface premium."""
    def password_entered():
        if "password" in st.session_state and st.session_state["password"] == st.secrets.get("PASSWORD", "admin"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        # Centrage de l'interface
        st.markdown("<br><br>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 2, 1])
        
        with col:
            if os.path.exists("ba7ath.png"):
                st.image("ba7ath.png", width='stretch')
            
            st.markdown("""
                <div style='text-align: center; border: 1px solid #e6e6e6; padding: 30px; border-radius: 15px; 
                            background-color: #ffffff; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-bottom: 20px;'>
                    <h1 style='color: #00457C; font-family: sans-serif; margin-bottom: 5px;'>Ba7ath Tn Scrapers</h1>
                    <h3 style='color: #4a4a4a; font-family: sans-serif; font-weight: normal; margin-top: 0;'>Intelligence Analytique (Data)</h3>
                    <p style='color: #888; font-style: italic; font-size: 0.9em; margin-top: 20px;'>
                        Plateforme sécurisée d'investigation OSINT & Collecte de données.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            st.text_input("Veuillez saisir le code d'accès investigation :", 
                         type="password", on_change=password_entered, key="password",
                         placeholder="Code secret...")
            
            if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                st.error("❌ Code d'accès incorrect. Veuillez réessayer.")
            
            st.info("⚠️ L'accès à cette console est réservé aux analystes autorisés.")
            
        return False
    return True
