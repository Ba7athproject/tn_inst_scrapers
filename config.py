import asyncio
import sys
import os

def initialize_system():
    """Initialise les politiques système pour Windows et Playwright."""
    # Correction de l'erreur NotImplementedError pour Playwright sur Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # ── FIX PyInstaller : forcer Playwright à trouver les navigateurs ──
        # Quand l'app tourne depuis un .exe PyInstaller, Playwright cherche
        # les navigateurs dans le dossier temporaire _MEI au lieu du chemin
        # système. On force le chemin standard ms-playwright.
        pw_sys_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ms-playwright")
        if os.path.exists(pw_sys_path):
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = pw_sys_path
        else:
            # Si les navigateurs ne sont pas encore installés, on tente l'install
            print("⚠️ Navigateurs Playwright introuvables. Installation en cours...")
            os.system("playwright install chromium")
            if os.path.exists(pw_sys_path):
                os.environ["PLAYWRIGHT_BROWSERS_PATH"] = pw_sys_path
    else:
        # Installation des binaires Chromium sur Streamlit Cloud au premier lancement
        if not os.path.exists(os.path.expanduser("~/.cache/ms-playwright")):
            os.system("playwright install chromium")
    
    # Autres initialisations possibles (logs, dossiers temporaires, etc.)
    if not os.path.exists("debug"):
        os.makedirs("debug", exist_ok=True)

