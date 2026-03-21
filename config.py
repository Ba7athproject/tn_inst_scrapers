import asyncio
import sys
import os

def initialize_system():
    """Initialise les politiques système pour Windows et Playwright."""
    # Correction de l'erreur NotImplementedError pour Playwright sur Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Autres initialisations possibles (logs, dossiers temporaires, etc.)
    if not os.path.exists("debug"):
        os.makedirs("debug", exist_ok=True)
