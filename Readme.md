# 🔍 Ba7ath Edge Pro (Standalone Edition v9.0)

**Ba7ath Edge Pro** est une suite d'intelligence économique et d'investigation numérique (OSINT) spécialisée pour le marché tunisien. Cette version **v9.0** marque le passage à une plateforme autonome, brandée et équipée de l'investigateur JORT.

---

## 🏛️ L'Écosystème Ba7ath PRO

Le projet s'articule autour de trois modules majeurs :

### 1. ⚖️ Investigateur JORT (Nouveau)
Scraping intelligent du Journal Officiel de la République Tunisienne.
- **Moteur Vaadin/Playwright** : Navigation asynchrone pour extraire les annonces légales complexes.
- **Filtres Avancés** : Recherche par catégorie (Constitution, Actes, etc.) et périodes multi-années.
- **Gestion JortSearch** : Intégration transparente de vos identifiants JortSearch.

### 2. 🏛️ Edge Scraper TUNEPS
Moteur de scraping "Haute Fidélité" pour les marchés publics.
- **WAF Bypass & Anti-Ban** : Émulation humaine pour naviguer sur le portail TUNEPS sans interruption.
- **Détails Profonds** : Extraction automatique des gagnants, RNE, montants et motifs de décision.
- **Vivid UI** : Interface "Slate & Azure" avec signalisation dynamique du statut système.

### 3. 🍱 Mode Standalone & Portabilité
- **Zéro Dépendance** : Distribué en un seul fichier `.exe` pour Windows. Aucun Python requis.
- **Build Automatisé** : Script `build_standalone.py` inclus pour générer l'exécutable personnalisé.

---

## 🚀 Installation & Lancement

### Pour les utilisateurs finaux
L'exécutable se trouve dans le dossier `dist/Ba7ath_Edge_Pro.exe`. Double-cliquez pour lancer.

### Pour les développeurs
1. **Prérequis** : Python 3.10+, Playwright.
2. **Installation** : `pip install -r requirements.txt`
3. **Lancement** : `python tuneps_gui.py`
4. **Compilation** : `python build_standalone.py`

---

## 🏗️ Architecture Technique

- **Moteurs** : Playwright (JORT) & Aiohttp (TUNEPS).
- **Interface** : Tkinter Premium avec Thème Slate & Azure.
- **Export** : Excel (.xlsx) via Pandas.

---

## 🛡️ Éthique & Responsabilité
Ce projet respecte les standards de transparence OSINT. Les utilisateurs doivent respecter les conditions d'utilisation des sites sources.

*(c) 2026 Ba7athproject - Standard de vérification OSINT Tunisie.*