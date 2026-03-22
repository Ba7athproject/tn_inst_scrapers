import streamlit as st
import os
import requests
import urllib3

# Désactiver les avertissements SSL pour les tests de diagnostic
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def render_settings():
    st.header("⚙️ Paramètres & Diagnostic")
    st.write("**Projet :** Ba7ath - Investigation & Scrapers")
    st.write("**Version :** 7.5 (Dynamic Proxy + Network Debug)")
    
    st.divider()
    
    # --- SECTION LOGOUT ---
    if st.button("🚪 Déconnexion (Logout)", width='stretch'):
        del st.session_state["password_correct"]
        st.rerun()
        
    st.divider()
    
    # --- SECTION LISTE DE PROXYS (ROTATION) ---
    st.subheader("🔄 Liste de Rotation (Multi-Proxys)")
    st.markdown("""
        Ajoutez plusieurs proxys (un par ligne) pour activer la rotation automatique. 
        Le format recommandé est `http://ip:port`.
    """)
    
    # Valeurs par défaut (Elite proxies extraits précédemment)
    elite_defaults = [
        "http://121.126.185.63:25152",
        "http://38.145.218.134:8443",
        "http://38.145.220.40:8443",
        "http://38.145.220.65:8443",
        "http://194.67.99.223:1080",
        "http://15.188.75.223:3128",
        "http://13.230.49.39:8080",
        "http://104.168.158.236:10808",
        "http://38.145.220.33:8448",
        "http://38.145.220.34:8443"
    ]
    
    if "proxy_list" not in st.session_state:
        st.session_state["proxy_list"] = elite_defaults
        
    proxy_list_text = st.text_area(
        "Proxys à utiliser pour la rotation",
        value="\n".join(st.session_state["proxy_list"]),
        height=200,
        help="Saisissez un proxy par ligne. Le moteur TUNEPS les utilisera à tour de rôle."
    )
    
    new_list = [p.strip() for p in proxy_list_text.split("\n") if p.strip()]
    if new_list != st.session_state["proxy_list"]:
        st.session_state["proxy_list"] = new_list
        st.success(f"✅ Liste mise à jour ({len(new_list)} proxys chargés).")

    if st.button("🔍 Trouver le premier proxy fonctionnel dans la liste", help="Teste chaque proxy de la liste un par un jusqu'à en trouver un qui répond."):
        _scan_proxy_list(st.session_state["proxy_list"])

    st.divider()
    
    # --- SECTION DIAGNOSTIC ---
    st.subheader("🛰️ Diagnostic Réseau (WAF TUNEPS)")
    
    # Priorité au proxy manuel pour le test unitaire, sinon premier de la liste
    current_proxy = st.session_state.get("manual_proxy")
    if not current_proxy and st.session_state["proxy_list"]:
        current_proxy = st.session_state["proxy_list"][0]
        
    if current_proxy:
        st.info(f"🛰️ **Proxy Actif pour le test :** `{str(current_proxy)}`")
    else:
        st.warning("⚠️ **Aucun proxy saisi.** Utilisation de l'IP directe du serveur.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Lancer le test complet", type="primary", width='stretch'):
            if current_proxy and not (current_proxy.startswith('http') or current_proxy.startswith('socks')):
                st.error("❌ Format de proxy invalide.")
            else:
                _run_network_diagnostic(current_proxy)
    with col2:
        if st.button("🧹 Vider la mémoire", width='stretch'):
            st.session_state["manual_proxy"] = ""
            st.rerun()

def _scan_proxy_list(proxies):
    """Teste la liste jusqu'à trouver un proxy vivant."""
    with st.status("Recherche d'un proxy valide...", expanded=True) as status:
        found = False
        for p in proxies:
            st.write(f"⏳ Test de `{p}`...")
            try:
                # Timeout très court (3s) pour passer vite aux suivants si le proxy est lent
                proxies_dict = {"http": p, "https": p}
                resp = requests.get("https://api.ipify.org?format=json", proxies=proxies_dict, timeout=4)
                if resp.status_code == 200:
                    ip = resp.json().get('ip')
                    st.success(f"💎 Proxy opérationnel trouvé ! IP: {ip}")
                    st.session_state["manual_proxy"] = p
                    found = True
                    break
            except:
                st.write(f"❌ `{p}` ne répond pas.")
        
        if found:
            status.update(label="Proxy trouvé et configuré !", state="complete", expanded=False)
            st.rerun()
        else:
            status.update(label="Aucun proxy fonctionnel dans la liste.", state="error")
            st.error("📉 Tous les proxys de la liste ont échoué. Essayez de récupérer une nouvelle liste fraîche.")


def _run_network_diagnostic(proxy_url):
    # Dictionnaire de proxies pour 'requests'
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    
    with st.status("Analyse du réseau en cours...", expanded=True) as status:
        # 1. TEST IP PUBLIQUE
        try:
            st.write("🔍 Interrogation du service IP...")
            # On force le timeout car un mauvais proxy peut mettre longtemps à répondre
            resp_ip = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=12)
            my_ip = resp_ip.json().get('ip', 'Inconnu')
            st.success(f"✅ **IP Détectée :** {my_ip}")
        except Exception as e:
            st.error(f"❌ **Échec IP :** Impossible de joindre le proxy ou internet ({e})")
            status.update(label="Diagnostic échoué.", state="error")
            return

        # 2. TEST TUNEPS WAF
        try:
            st.write("🕊️ Tentative d'accès au portail TUNEPS...")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp_tn = requests.get(
                "https://www.marchespublics.gov.tn/fr/resultats", 
                headers=headers, 
                proxies=proxies, 
                timeout=15, 
                verify=False
            )
            
            if resp_tn.status_code == 200:
                html = resp_tn.text.lower()
                if "access denied" in html or "rejected" in html:
                    st.error("🚫 **Verdict : BANNI (IP bloquée par F5 BIG-IP)**")
                elif "captcha" in html or "distil_captcha" in html:
                    st.warning("🤖 **Verdict : CAPTCHA (Vérification forcée)**")
                else:
                    st.success("💎 **Verdict : ACCÈS OK (IP acceptée)**")
            else:
                st.error(f"❌ **Verdict : ERREUR HTTP {resp_tn.status_code}**")
                
        except Exception as e:
            st.error(f"❌ **Verdict : TUNEPS INJOIGNABLE ({e})**")
            
        status.update(label="Diagnostic terminé.", state="complete", expanded=False)
