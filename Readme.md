# 🔍 Ba7ath Edge Pro (Standalone Edition v9.0)

**Ba7ath Edge Pro** est une suite d'intelligence économique et d'investigation numérique (OSINT) avancée, conçue pour automatiser la collecte, l'enrichissement et le croisement des données publiques tunisiennes.

Indispensable pour le data-journalisme et l'analyse stratégique, ce projet offre une réponse technique robuste aux défis d'extraction institutionnelle (WAF complexes, Shadow DOM et protection anti-robot).

---

## 🏛️ L'Écosystème Ba7ath EDGE

Le projet s'articule autour de trois piliers technologiques majeurs :

### 1. 🛡️ Scraper Pro TUNEPS (`tuneps_gui.py`)
Moteur d'extraction "Haute Fidélité" pour les marchés publics tunisiens.
- **WAF Bypass** : Contournement du pare-feu F5 BIG-IP via une émulation de navigation réelle.
- **Détails Profonds** : Extraction automatique des attributaires, RNE, montants HT/TTC et motifs de décision.
- **Interface Premium** : Design Slate & Azure avec signalisation dynamique de l'état (Vert/Orange).

### 2. ⚖️ Investigateur JORT (`jort_investigator.py`)
Scraping intelligent du Journal Officiel de la République Tunisienne.
- **Moteur Vaadin/Playwright** : Navigation asynchrone pour extraire les annonces légales complexes (Constitutions, Fonds de commerce, etc.).
- **Filtres Avancés** : Recherche par catégorie thématique et balayage temporel multi-années.
- **Autonomie Totale** : Fonctionnement 100% local pour garantir la discrétion des enquêtes.

### 3. 🏢 Moteur RNE Explorer (`rne_investigator.py`)
Module d'exploration profonde du Registre National des Entreprises.
- **Ciblage Spécifique** : Identification des structures Ahliyas et autres entités juridiques stratégiques.
- **Enrichissement** : Récupération des données d'identification et historiques des sociétés.

---

## 🍱 Mode Standalone & Portabilité (v9.0)

L'application est désormais optimisée pour une utilisation sans installation technique :
- **Fichier Unique** : Distribué en un seul fichier `.exe` pour Windows. Aucun Python requis.
- **Assets Intégrés** : Le logo, l'icône système et la base de données des acheteurs (`buyers.json`) sont tous packagés dans l'exécutable.

---

## 🚀 Installation & Lancement

### Pour les Utilisateurs Finaux
Téléchargez la dernière Release : `Ba7ath_Edge_Pro.exe` dans le dossier `dist/`. Double-cliquez pour lancer.

### Pour les Développeurs
1. **Installation** : `pip install -r requirements.txt`
2. **Setup Navigateurs** : `playwright install chromium`
3. **Lancement Hub Web** : `streamlit run app_ba7ath.py`
4. **Lancement Scraper Local** : `python tuneps_gui.py`
5. **Compilation** : `python build_standalone.py`

---

## 🏗️ Architecture Technique
- **Backends** : Playwright (JORT), Aiohttp (TUNEPS), Requests (RNE).
- **Frontends** : Streamlit (Hub Web) & Tkinter (Standalone Pro).
- **Data** : Export Excel (.xlsx) et CSV standardisés.

---

## 🛡️ Éthique OSINT
Ce projet respecte les standards de transparence et de responsabilité. Les utilisateurs doivent se conformer aux conditions d'utilisation des plateformes institutionnelles sources.

*(c) 2026 Ba7athproject - Standard de vérification OSINT Tunisie.*