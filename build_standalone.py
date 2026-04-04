import PyInstaller.__main__
import os
import sys

# Nom de l'exécutable final
APP_NAME = "Ba7ath_Edge_Pro"
ICON_PATH = "ba7ath.ico"
LOGO_PATH = "ba7ath.png"
DB_PATH = "buyers.json"

# ── EXCLUSIONS MASSIVES ──
# L'environnement Python global contient des centaines de packages lourds
# (ML, AI, Web frameworks...) qui ne sont PAS utilisés par l'app.
# Sans ces exclusions, le build dure >30 min et l'exe fait plusieurs Go.
EXCLUDES = [
    # ── ML / AI / Deep Learning (>2 Go à eux seuls) ──
    "tensorflow", "tf_keras", "keras",
    "torch", "torchvision", "torchaudio",
    "transformers", "tokenizers", "safetensors", "accelerate",
    "ultralytics",
    "sklearn", "scikit-learn", "lightgbm", "xgboost",
    "spacy", "thinc", "srsly", "cymem", "preshed", "blis",
    "nltk", "gensim",
    "langchain", "langchain_core", "langchain_community", "langchain_text_splitters",
    "openai", "anthropic", "cohere",
    "onnxruntime", "onnx",
    "numba", "llvmlite",
    "modelscope",
    "bitsandbytes",
    "lightning", "pytorch_lightning",
    "datasets", "evaluate", "huggingface_hub",
    
    # ── Computer Vision / Audio / Video ──
    "cv2", "opencv-python",
    "librosa", "soundfile", "sounddevice", "audioread",
    "av",
    "yt_dlp",
    "pyppeteer",
    "pydub",
    
    # ── Web Frameworks (pas besoin de Django/Flask pour une app tkinter) ──
    "django",
    "flask", "werkzeug",
    "fastapi", "uvicorn", "starlette",
    
    # ── Jupyter / Notebooks ──
    "jupyter", "jupyterlab", "notebook", "nbconvert", "nbformat",
    "ipykernel", "ipywidgets", "IPython",
    
    # ── Data Science lourds non utilisés ──
    "dask",
    "plotly",  # Non utilisé dans tuneps_gui.py (seulement Streamlit)
    "altair",
    "matplotlib",  # Non utilisé dans la GUI tkinter
    "sympy",
    "pyarrow",
    "shapely",
    "scipy",  # Si pas directement utilisé
    "numexpr",
    "tables",
    
    # ── Bases de données non utilisées ──
    "sqlalchemy", "alembic",
    "psycopg2",
    "pymongo", "motor",
    "redis",
    "duckdb",
    
    # ── GUI Frameworks concurrents (on utilise tkinter natif) ──
    "PyQt5", "PyQt6", "PySide2", "PySide6",
    "wx",
    
    # ── Streamlit (pas dans l'exe standalone, c'est tkinter) ──
    "streamlit", "streamlit_option_menu",
    
    # ── Crypto / Sécurité non essentiels ──
    "Crypto", "Cryptodome",
    
    # ── Divers non utilisés ──
    "selenium",
    "scrapy",
    "docutils",
    "reportlab",
    "pdfminer",
    "pypdfium2",
    "ruamel",
    "sentry_sdk",
    "opentelemetry",
    "grpc", "grpcio",
    "google.cloud", "google.api_core",
    "mako",
    "sacremoses",
    "fake_useragent",
    "ddgs",
    "markdown",
    "tinycss2",
    "babel",
    "mistune",
    "argon2",
    "lxml",
    "zmq", "pyzmq",
    "tornado",
    "bokeh",
    "seaborn",
    "wordcloud",
    "folium",
    "geopy",
    "pydantic",
    "orjson", "ormsgpack",
    "anyio", "sniffio",
    "httpx", "httpcore",
    "fsspec",
    "rich",
    "pygments",
]

def build():
    print(f"🚀 Démarrage du Build Standalone pour {APP_NAME}...")
    print(f"📦 {len(EXCLUDES)} packages exclus pour optimiser la taille.")
    
    # Arguments PyInstaller
    args = [
        'tuneps_gui.py',                 # Script principal
        '--name=%s' % APP_NAME,          # Nom de l'app
        '--onefile',                     # Un seul fichier .exe
        '--windowed',                    # Pas de console
        '--clean',                       # Nettoyer le cache
        '--noconfirm',                   # Écraser sans demander
    ]
    
    # Exclusions
    for mod in EXCLUDES:
        args.append('--exclude-module=%s' % mod)
    
    # Ajout de l'icône si elle existe
    if os.path.exists(ICON_PATH):
        args.append('--icon=%s' % ICON_PATH)
    
    # Ajout des ressources (logo, json)
    if os.path.exists(LOGO_PATH):
        args.append('--add-data=%s;.' % LOGO_PATH)
    
    if os.path.exists(DB_PATH):
        args.append('--add-data=%s;.' % DB_PATH)

    PyInstaller.__main__.run(args)
    
    exe_path = os.path.join("dist", f"{APP_NAME}.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n✅ Build Terminé ! Taille : {size_mb:.1f} Mo")
        print(f"📂 {os.path.abspath(exe_path)}")
    else:
        print(f"\n✅ Build Terminé ! L'exécutable se trouve dans le dossier 'dist/'.")

if __name__ == "__main__":
    build()
