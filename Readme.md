📖 Documentation Technique : Console ba7ath (Extracteur RNE & JORT)
1. Présentation de l'Outil
La Console ba7ath est un outil d'investigation numérique (OSINT) automatisé, développé en Python. Il est conçu spécifiquement pour les journalistes d'investigation et les chercheurs travaillant sur le contexte tunisien.

L'outil permet de collecter, d'enrichir et de croiser des données publiques provenant de deux sources majeures :

RNE (Registre National des Entreprises) : Moissonnage des données légales et métadonnées des entreprises.

JORT (Journal Officiel de la République Tunisienne) : Scraping des annonces légales (créations, modifications, ventes de fonds de commerce).

Objectif Pédagogique : Démontrer comment automatiser la collecte d'informations publiques tout en surmontant les défis techniques des sites web modernes (API non documentées, interfaces asynchrones Vaadin).

2. Architecture Technique et Méthodologie
L'application repose sur une architecture modulaire composée de trois blocs principaux :

A. Moteur RNE (RNECore) : Ingénierie Inverse d'API
Ce module interroge directement l'API REST publique du RNE en deux phases :

Phase de Découverte (Short Entities) : Utilisation de requêtes GET avec le paramètre de pagination afterId pour contourner les limites de requêtes et récupérer tous les identifiants uniques correspondant à un mot-clé (ex: "Société communautaire").

Phase d'Enrichissement (Short Details) : Extraction exhaustive des fiches (14 points de données, incluant les adresses reconstruites en arabe et français, la forme juridique et le statut).

B. Moteur JORT (JORTScraper) : Scraping Asynchrone (Playwright)
Le site du JORT utilise le framework Vaadin Flow, qui génère le DOM dynamiquement via JavaScript, rendant les outils classiques (BeautifulSoup, Requests) inopérants.

Pilotage de Navigateur : Utilisation de Playwright en mode headless pour simuler une navigation humaine.

Auto-Pagination Intelligente : Détection du compteur de résultats via une expression régulière (\d+\s*-\s*\d+\s+(?:of|sur|de|من)\s+\d+) pour calculer dynamiquement le nombre de pages à extraire.

Extraction Profonde : Utilisation de la méthode .evaluate() pour lire les propriétés JavaScript internes des web components (node.title, node.subTitle) qui n'apparaissent pas dans le code HTML source.

C. Module d'Analyse et de Consolidation (Pandas)
Fusion : Nettoyage et déduplication des jeux de données basés sur les clés primaires (ID Unique pour le RNE, ID_JORT pour le JORT).

Data Visualisation : Génération de graphiques dynamiques adaptatifs selon la source des données (répartition géographique pour le RNE, répartition par journal pour le JORT).

3. Prérequis et Installation
Environnement Requis
Python 3.10 ou supérieur.

Système d'exploitation : Windows, macOS ou Linux.

Dépendances (Requirements)
Plaintext
streamlit
pandas
requests
playwright
streamlit-option-menu
Étapes d'installation
Cloner le projet et installer les bibliothèques :

Bash
pip install -r requirements.txt
Installer les navigateurs pour Playwright :

Bash
playwright install chromium
Configurer les accès sécurisés :
Créer un dossier .streamlit à la racine du projet, puis un fichier secrets.toml contenant vos identifiants :

Ini, TOML
PASSWORD = "votre_mot_de_passe_console"
JORT_USER = "votre_identifiant_jort"
JORT_PASS = "votre_mot_de_passe_jort"
Lancer l'application :

Bash
streamlit run app_ba7ath.py
4. Bonnes Pratiques et Ethique OSINT
Ce script a été conçu dans le respect absolu des standards journalistiques :

Sources Publiques : L'outil n'interroge que des bases de données ouvertes au public. Aucune donnée privée n'est ciblée.

Transparence : L'en-tête de requête (User-Agent) déclare clairement la nature de la requête, et des délais (time.sleep et asyncio.sleep) sont intégrés pour ne pas surcharger les serveurs gouvernementaux (prévention du déni de service involontaire).

Rigueur des Données : La fonction _clean() assure que les pollutions de données (valeurs "null", points isolés) sont systématiquement purgées pour garantir l'intégrité de l'analyse ultérieure.