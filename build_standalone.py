import PyInstaller.__main__
import os
import sys

# Nom de l'exécutable final
APP_NAME = "Ba7ath_Edge_Pro"
ICON_PATH = "ba7ath.ico"
LOGO_PATH = "ba7ath.png"
DB_PATH = "buyers.json"

def build():
    print(f"🚀 Démarrage du Build Standalone pour {APP_NAME}...")
    
    # Arguments PyInstaller
    args = [
        'tuneps_gui.py',                 # Script principal
        '--name=%s' % APP_NAME,          # Nom de l'app
        '--onefile',                     # Un seul fichier .exe
        '--windowed',                    # Pas de console (UI seulement)
        '--clean',                       # Nettoyer le cache
    ]
    
    # Ajout de l'icône si elle existe
    if os.path.exists(ICON_PATH):
        args.append('--icon=%s' % ICON_PATH)
    
    # Ajout des ressources (logo, json)
    # Syntaxe : --add-data "source;destination" (Windows utilise ;)
    if os.path.exists(LOGO_PATH):
        args.append('--add-data=%s;.' % LOGO_PATH)
    
    if os.path.exists(DB_PATH):
        args.append('--add-data=%s;.' % DB_PATH)

    # Note : On ignore core_rne.py si pas utilisé directement par tuneps_gui
    # Mais PyInstaller analyse les imports automatiquement.
    
    PyInstaller.__main__.run(args)
    print(f"\n✅ Build Terminé ! L'exécutable se trouve dans le dossier 'dist/'.")

if __name__ == "__main__":
    build()
