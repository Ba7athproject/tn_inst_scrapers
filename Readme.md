# 🔍 Ba7ath Tn Scraper Hub (Pro Edition v7.7)

**Ba7ath Tn Scraper Hub** est un écosystème d'investigation numérique (OSINT) avancé, conçu pour automatiser la collecte, l'enrichissement et le croisement des données publiques tunisiennes.

Indispensable pour le data-journalisme et l'intelligence économique, ce projet offre une réponse technique robuste aux défis modernes (WAF complexes, API asynchrones, et protection anti-robot).

---

## 🏛️ L'Écosystème Ba7ath PRO

Le projet s'articule autour de trois piliers technologiques :

### 1. ⚛️ Streamlit Analytics Hub (`app_ba7ath.py`)
Le quartier général analytique de l'investigation.
- **Moteur RNE** : Extraction profonde des registres d'entreprises (après découverte par `afterId`).
- **Moteur JORT** : Scraping asynchrone via Playwright (Headless) pour naviguer dans les annonces légales Vaadin.
- **Module de Fusion** : Interconnexion dynamique entre TUNEPS, RNE et JORT.

### 2. 🛡️ Edge Scraper Pro (`tuneps_gui.py`)
Moteur de scraping local "Haute Fidélité" pour les marchés publics (TUNEPS).
- **WAF Bypass** : Contournement du pare-feu F5 BIG-IP via une émulation de navigation réelle.
- **Anti-Ban Intelligent** : Gestion automatique des délais et pauses de sécurité (Rate-limiting).
- **Indexation Massive** : Intégration de plus de **1100 acheteurs publics** et extraction des détails profonds (Gagnants, RNE, Montants, Motifs).
- **Version Portable** : Compilable en `.exe` pour une utilisation locale sur Windows.

### 3. 🧠 Centre d'Intelligence Analytique (`view_analyse.py`)
Un outil d'exploration flexible pour transformer les données brutes en insights.
- **Analyse Automatique** : Détection des KPIs, top-acheteurs, et statistiques de marché.
- **Visualisation Dynamique** : Graphiques Plotly interactifs pour croiser et explorer n'importe quel dataset (Excel/CSV).
- **Pont de Données** : Importation directe depuis le Hub TUNEPS en un clic.

---

## 🚀 Installation & Lancement

### Prérequis
- **Python 3.10+**
- **Navigateurs Playwright** (pour le JORT) : `playwright install chromium`

### Setup Rapide
```bash
# Installation des dépendances
pip install -r requirements.txt

# Lancement de la Console Web
streamlit run app_ba7ath.py

# Lancement du Scraper Pro (Local)
python tuneps_gui.py
```

---

## 🏗️ Architecture Technique

- **Backend** : Python (Pandas, Aiohttp, Playwright, Curl_cffi)
- **Frontend Web** : Streamlit (Branding Ba7ath Indigo)
- **Frontend GUI** : Tkinter (Structure Notebook extensible)
- **Data Persistence** : Exports Excel/CSV standardisés pour l'interopérabilité.

---

## 🛡️ Éthique & Bonnes Pratiques OSINT
Ce projet respecte les standards de transparence et de responsabilité liés à l'extraction de données publiques :
- **Sources Ouvertes** : Uniquement des données accessibles librement par tout internaute.
- **Rate-Limiting** : Des pauses sont intégrées pour ne pas surcharger les ressources des serveurs gouvernementaux.
- **Intégrité** : Tous les fichiers de debug et temporaires sont exclus (`.gitignore`) pour un dépôt GitHub sain et professionnel.

---
*(c) 2026 Ba7athproject - Standard de vérification OSINT Tunisie.*