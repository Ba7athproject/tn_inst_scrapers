import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import aiohttp
import pandas as pd
import ssl
import random
import time
import threading
import os
import json
import sys
from datetime import datetime
from bs4 import BeautifulSoup
try:
    from PIL import Image, ImageTk
except ImportError:
    # Fallback si Pillow n'est pas installé (quoique recommandé)
    Image, ImageTk = None, None

# ── FIX PyInstaller : Forcer Playwright à trouver les navigateurs système ──
# Sans ce fix, l'exe cherche Chromium dans le dossier temporaire _MEI.
if sys.platform == 'win32':
    _pw_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ms-playwright")
    if os.path.exists(_pw_path):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _pw_path

from jort_investigator import JORTScraper

# --- GESTION DES RESSOURCES (Icones, JSON) ---
def resource_path(relative_path):
    """ Obtenir le chemin absolu vers la ressource, compatible PyInstaller """
    try:
        # PyInstaller crée un dossier temporaire _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- CONFIGURATION DES ACHETEURS ---
# (Intégration simplifiée ou lecture de buyers.json si présent)
def load_buyers():
    buyers = {"Tous": ""}
    try:
        path = resource_path("buyers.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                buyers.update(json.load(f))
    except: pass
    return buyers

# --- LOGIQUE CORE TUNEPS (VERSION HAUTE FIDÉLITÉ) ---

class TunepsLogic:
    def __init__(self, log_callback):
        self.base_url = "https://www.marchespublics.gov.tn/fr/resultats"
        # En-têtes de base imitant parfaitement un Chrome moderne sur Windows
        self.common_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"'
        }
        # En-têtes pour les appels AJAX (Recherche)
        self.headers = self.common_headers.copy()
        self.headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.marchespublics.gov.tn/fr/resultats",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        })
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.log = log_callback

    async def _fetch_details(self, session, award_id):
        url = f"{self.base_url}/{award_id}"
        # On retire l'en-tête AJAX pour la page de détail (page HTML complète)
        detail_headers = self.headers.copy()
        if "X-Requested-With" in detail_headers:
            del detail_headers["X-Requested-With"]
            
        try:
            async with session.get(url, headers=detail_headers, timeout=15) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    if not html or len(html) < 500:
                        self.log(f"⚠️ Page de détail vide pour {award_id}")
                        return {}
                    soup = BeautifulSoup(html, 'html.parser')
                    details = {}
                    # TUNEPS utilise souvent des tables ou des structures clés/valeurs
                    for row in soup.find_all(['tr', 'li']):
                        cells = row.find_all(['td', 'th', 'span'])
                        if len(cells) >= 2:
                            k = cells[0].text.strip().lower()
                            v = cells[1].text.strip()
                            # Nettoyage des caractères invisibles
                            k = k.replace('\xa0', ' ').replace(':', '').strip()
                            
                            if any(x in k for x in ["titulaire", "attributaire", "gagnant", "raison sociale"]):
                                details["Gagnant"] = v
                            elif any(x in k for x in ["rne", "identifiant national", "identifiant de l'établissement"]):
                                details["RNE"] = v
                            elif "montant ht" in k: details["HT"] = v
                            elif "montant ttc" in k: details["TTC"] = v
                            elif "nationalité" in k: details["Nat"] = v
                            elif "forme juridique" in k or "personnalité" in k: details["Forme"] = v
                            elif "région" in k: details["Reg"] = v
                    
                    if not details:
                        # Si aucun label standard n'est trouvé, c'est peut-être un dossier Sans Suite ou Annulé
                        self.log(f"ℹ️ Structure spéciale pour {award_id} (Dossier possiblement infructueux/sans suite)")
                        
                    return details
        except Exception as e:
            self.log(f"⚠️ Erreur détail {award_id}: {e}")
        return {}

    async def run_scrape(self, keyword, limit, date_from, date_to, status_id, sme_id, buyer_id):
        self.log(f"🚀 Début Scraping local. Cible : '{keyword}'...")
        params = {
            'draw': '1', 'start': '0', 'length': str(limit), 'keywords': keyword,
            'publication_date_from': date_from, 'publication_date_to': date_to,
            'award_category': status_id, 'sme': sme_id, 'organization': buyer_id
        }
        params = {k: v for k, v in params.items() if v} # Clean empty
        
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context)) as session:
            try:
                # 1. Navigation Initiale (Simulation Document) pour les cookies WAF
                nav_headers = self.common_headers.copy()
                nav_headers.update({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=1.0,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1"
                })
                async with session.get(self.base_url, headers=nav_headers) as _:
                    await asyncio.sleep(min(1.5, random.uniform(0.8, 2.0)))
                
                # 2. On lance la recherche réelle (AJAX)
                async with session.get(self.base_url, headers=self.headers, params=params) as resp:
                    if resp.status != 200:
                        self.log(f"❌ Erreur WAF (HTTP {resp.status})")
                        return None
                    
                    raw_text = await resp.text()
                    try:
                        json_data = json.loads(raw_text)
                    except Exception:
                        # On logue un extrait pour comprendre pourquoi ce n'est pas du JSON
                        self.log(f"❌ Données reçues non-JSON (Blocage possible)")
                        if "security" in raw_text.lower() or "blocked" in raw_text.lower():
                            self.log("⚠️ Le WAF de TUNEPS a bloqué la requête locale.")
                        else:
                            self.log(f"Extrait : {raw_text[:150]}...")
                        return None
            except Exception as e:
                self.log(f"❌ Impossible de joindre TUNEPS : {e}")
                return None

            records = json_data.get('data', [])[:limit]
            if not records:
                self.log("ℹ️ Aucun résultat trouvé pour ces critères.")
                return None

            self.log(f"📦 {len(records)} dossiers trouvés. Extraction des détails profonds...")
            
            sem = asyncio.Semaphore(1) # Un seul à la fois pour plus de sécurité
            async def job(idx, aw_id):
                async with sem:
                    # On ralentit pour l'IP locale afin d'éviter le blocage WAF (Moyenne 3.5s)
                    await asyncio.sleep(random.uniform(2.5, 4.5))
                    
                    # Pause supplémentaire tous les 15 dossiers (BATCH PAUSE)
                    if idx > 0 and idx % 15 == 0:
                        self.log(f"⏸️ Pause de sécurité anti-ban (10s) après {idx} dossiers...")
                        await asyncio.sleep(10)
                        
                    return await self._fetch_details(session, aw_id)

            tasks = [job(i, r.get('id', '')) for i, r in enumerate(records)]
            details_list = await asyncio.gather(*tasks)

            final_data = []
            for i, r in enumerate(records):
                det = details_list[i]
                lot = r.get('lot', {})
                tender = lot.get('tender', {})
                org = tender.get('organization', {})
                
                # Récupération de la catégorie lisible
                cat_id = str(r.get('award_category', ''))
                cat_label = "Attribué" if cat_id == "157" else ("Infructueux" if cat_id == "158" else ("Annulé" if cat_id == "156" else "Autre"))

                # Récupération sécurisée du motif
                motif = r.get('motif_fr') or r.get('motif') or "N/A"
                if motif == "N/A" and cat_id in ["158", "156"]:
                    # Parfois le motif est dans le lot
                    motif = lot.get('motif_fr') or lot.get('motif') or "N/A"

                final_data.append({
                    "ID Marché": r.get('id', 'N/A'),
                    "Date de publication": r.get('publication_date', 'Inconnue'),
                    "Acheteur Public": org.get('name_fr', org.get('name', 'Inconnue')),
                    "Objet de l'appel d'offres": tender.get('title_fr', tender.get('title', 'Indisponible')),
                    "Lot / Article": lot.get('description_fr') or lot.get('title_fr') or "N/A",
                    "Catégorie de résultat": cat_label,
                    "Attributaire (Gagnant)": det.get("Gagnant", "Non renseigné"),
                    "RNE": det.get("RNE", "N/A"),
                    "Montant HT": det.get("HT", "0.000"),
                    "Montant TTC": det.get("TTC", "0.000"),
                    "Personnalité juridique": det.get("Forme", "N/A"),
                    "Nationalité": det.get("Nat", "N/A"),
                    "Région": det.get("Reg", "N/A"),
                    "Motif": motif,
                    "Lien Source": f"https://www.marchespublics.gov.tn/fr/resultats/{r.get('id', '')}"
                })
            return pd.DataFrame(final_data)

class JortLogic:
    def __init__(self, log_callback):
        self.log = log_callback

    async def run_scrape(self, user, pwd, keywords, year_start, year_end, category, pages):
        self.log(f"🚀 Démarrage JORT ({year_start} -> {year_end}) - {category}...")
        scraper = JORTScraper(user, pwd, headless=True)
        try:
            # run_scrape crée son propre browser en interne
            df = await scraper.run_scrape(user, pwd, keywords, year_start, year_end, category, pages, logger=self.log)
            return df
        except Exception as e:
            self.log(f"❌ Erreur JORT : {e}")
            return None

# --- INTERFACE GUI PROFESSIONNELLE ---

class TunepsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ba7ath Edge Pro v8.5")
        self.root.geometry("1000x850")
        self.root.configure(bg="#f8fafc")
        
        self.buyers_data = load_buyers()
        self.buyer_names = sorted(list(self.buyers_data.keys()))

        # Configuration des Styles
        self.setup_styles()

        # Header Premium
        self.setup_header()

        # Conteneur Principal
        self.notebook = ttk.Notebook(root, style="Modern.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Onglet TUNEPS
        self.tuneps_tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(self.tuneps_tab, text=" 🏛️ TUNEPS ")
        self.setup_tuneps_tab()

        # Onglet JORT
        self.jort_tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(self.jort_tab, text=" ⚖️ JORT ")
        self.setup_jort_tab()

        # Onglet Paramètres
        self.settings_tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(self.settings_tab, text=" ⚙️ Paramètres ")
        self.setup_settings_tab()

        # Barre d'état (Status Bar Modernisée)
        self.status_var = tk.StringVar(value="PRÊT")
        self.status_bar = tk.Frame(root, bg="#f1f5f9", height=30)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.pack_propagate(False)
        
        ttk.Label(self.status_bar, textvariable=self.status_var, font=("Segoe UI", 8, "bold"), background="#f1f5f9", foreground="#64748b").pack(side=tk.LEFT, padx=20)
        
        # Divider ligne fine
        tk.Frame(self.status_bar, bg="#e2e8f0", height=15, width=1).pack(side=tk.LEFT, padx=10, fill=tk.Y, pady=5)
        
        self.engine_lbl = ttk.Label(self.status_bar, text="MOTEUR : PLAYWRIGHT/AIOHTTP", font=("Segoe UI", 7), background="#f1f5f9", foreground="#94a3b8")
        self.engine_lbl.pack(side=tk.LEFT, padx=10)

    def setup_header(self):
        header_bg = "#0f172a" # Deep Navy
        header = tk.Frame(self.root, bg=header_bg, height=70)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        # Logo Ba7ath
        logo_frame = tk.Frame(header, bg=header_bg)
        logo_frame.pack(side=tk.LEFT, padx=(30, 0))
        
        try:
            logo_path = resource_path("ba7ath.png")
            if os.path.exists(logo_path) and ImageTk:
                pil_img = Image.open(logo_path)
                # Redimensionnement proportionnel (Hauteur 45px)
                w, h = pil_img.size
                new_w = int(w * (45 / h))
                pil_img = pil_img.resize((new_w, 45), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(pil_img)
                tk.Label(logo_frame, image=self.logo_img, bg=header_bg).pack(side=tk.LEFT)
        except Exception as e:
            print(f"Erreur chargement logo: {e}")

        title_frame = tk.Frame(header, bg=header_bg)
        title_frame.pack(side=tk.LEFT, padx=15, pady=10)
        
        tk.Label(title_frame, text="BA7ATH EDGE PRO", font=("Segoe UI", 16, "bold"), fg="#ffffff", bg=header_bg).pack(side=tk.LEFT)
        tk.Label(title_frame, text="v9.0 | Standalone Edition", font=("Segoe UI", 9), fg="#3b82f6", bg=header_bg).pack(side=tk.LEFT, padx=15, pady=(5, 0))

        # Status Circle & Label
        self.status_frame = tk.Frame(header, bg=header_bg)
        self.status_frame.pack(side=tk.RIGHT, padx=30)
        self.status_dot = tk.Label(self.status_frame, text="●", fg="#10b981", bg=header_bg, font=("Arial", 14))
        self.status_dot.pack(side=tk.LEFT)
        self.status_label = tk.Label(self.status_frame, text="SYSTÈME PRÊT", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg=header_bg)
        self.status_label.pack(side=tk.LEFT, padx=5)

    def update_system_status(self, is_busy):
        """Met à jour visuellement l'état du système dans le header."""
        color = "#f59e0b" if is_busy else "#10b981" # Orange vs Vert
        text = "EXTRACTION EN COURS..." if is_busy else "SYSTÈME PRÊT"
        self.status_dot.configure(fg=color)
        self.status_label.configure(text=text)
        self.root.update_idletasks()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Palettes
        bg_main = "#f8fafc" # Slate 50
        card_bg = "#ffffff"
        accent = "#3b82f6"  # Azure Vibrant 500
        text_dark = "#1e293b" # Slate 900
        
        style.configure("Main.TFrame", background=bg_main)
        
        # Notebook & Tabs
        style.configure("Modern.TNotebook", background=bg_main, borderwidth=0)
        style.configure("Modern.TNotebook.Tab", padding=[25, 10], font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#64748b")
        style.map("Modern.TNotebook.Tab", 
                  background=[("selected", bg_main)], 
                  foreground=[("selected", accent)])
        
        # LabelFrames (Cards)
        style.configure("Card.TLabelframe", background=card_bg, borderwidth=1, relief="flat")
        style.configure("Card.TLabelframe.Label", background=card_bg, foreground=accent, font=("Segoe UI", 9, "bold"))
        
        # Labels
        style.configure("TLabel", background=bg_main, foreground=text_dark, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=card_bg, foreground=text_dark, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=bg_main, font=("Segoe UI", 18, "bold"), foreground=text_dark)
        
        # Buttons (Slim & Professional)
        style.configure("Action.TButton", font=("Segoe UI", 9, "bold"), padding=6, background=accent, foreground="white")
        style.map("Action.TButton", background=[("active", "#2563eb")])
        
        # Entries & Comboboxes
        style.configure("TEntry", fieldbackground="white", borderwidth=1)
        style.configure("TCombobox", fieldbackground="white", borderwidth=1)

    def setup_tuneps_tab(self):
        # Contenu
        content_frame = ttk.Frame(self.tuneps_tab, padding="30", style="Main.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Filtres Principaux
        filter_frame = ttk.LabelFrame(content_frame, text=" CONFIGURATION DE RECHERCHE ", style="Card.TLabelframe", padding="20")
        filter_frame.pack(fill=tk.X, pady=(0, 20))

        # On change la couleur de fond des enfants internes manuellement car ttk.LabelFrame est capricieux
        for child in filter_frame.winfo_children():
            try: child.configure(background="white")
            except: pass

        # Layout Grille pour filtres
        row = 0
        ttk.Label(filter_frame, text="Mots-clés :", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=8)
        self.ent_keywords = ttk.Entry(filter_frame, font=("Segoe UI", 10))
        self.ent_keywords.grid(row=row, column=1, sticky=tk.EW, padx=(15, 0), pady=8)
        filter_frame.columnconfigure(1, weight=1)

        row += 1
        ttk.Label(filter_frame, text="Acheteur Public :", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=8)
        self.cb_buyer = ttk.Combobox(filter_frame, values=["Tous"] + self.buyer_names, font=("Segoe UI", 10))
        self.cb_buyer.grid(row=row, column=1, sticky=tk.EW, padx=(15, 0), pady=8)
        self.cb_buyer.set("Tous")

        row += 1
        ttk.Label(filter_frame, text="Limite de résultats :", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=8)
        self.ent_limit = ttk.Entry(filter_frame, width=12, font=("Segoe UI", 10))
        self.ent_limit.grid(row=row, column=1, sticky=tk.W, padx=(15, 0), pady=8)
        self.ent_limit.insert(0, "50")

        # 2. Options Avancées (Période & Statut)
        adv_container = ttk.Frame(content_frame, style="Main.TFrame")
        adv_container.pack(fill=tk.X, pady=(0, 20))

        # Dates Card
        date_frame = ttk.LabelFrame(adv_container, text=" PÉRIODE ", style="Card.TLabelframe", padding="15")
        date_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(date_frame, text="Du :", style="Card.TLabel").grid(row=0, column=0, padx=5, pady=5)
        self.ent_from = ttk.Entry(date_frame, width=15)
        self.ent_from.grid(row=0, column=1, padx=5, pady=5)
        self.ent_from.insert(0, datetime.now().strftime("01/01/%Y"))
        self.ent_from.bind("<KeyRelease>", self._auto_format_date)
        
        ttk.Label(date_frame, text="Au :", style="Card.TLabel").grid(row=0, column=2, padx=5, pady=5)
        self.ent_to = ttk.Entry(date_frame, width=15)
        self.ent_to.grid(row=0, column=3, padx=5, pady=5)
        self.ent_to.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ent_to.bind("<KeyRelease>", self._auto_format_date)

        # Filtres Card
        status_frame = ttk.LabelFrame(adv_container, text=" FILTRES ", style="Card.TLabelframe", padding="15")
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(status_frame, text="Statut :", style="Card.TLabel").grid(row=0, column=0, padx=5, pady=5)
        self.cb_status = ttk.Combobox(status_frame, values=["Tous", "Attribué", "Infructueux", "Annulé"], state="readonly", width=12)
        self.cb_status.current(1)
        self.cb_status.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(status_frame, text="PME :", style="Card.TLabel").grid(row=0, column=2, padx=5, pady=5)
        self.cb_sme = ttk.Combobox(status_frame, values=["Tous", "Oui", "Non"], state="readonly", width=8)
        self.cb_sme.current(0)
        self.cb_sme.grid(row=0, column=3, padx=5, pady=5)

        # 3. Barre de Progression & Bouton
        action_frame = ttk.Frame(content_frame, style="Main.TFrame")
        action_frame.pack(fill=tk.X)

        self.progress = ttk.Progressbar(action_frame, orient=tk.HORIZONTAL, mode='determinate', style="Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, pady=(0, 15))

        self.btn_run = ttk.Button(action_frame, text="🚀 LANCER L'EXTRACTION", style="Action.TButton", command=self.start_thread)
        self.btn_run.pack(fill=tk.X, pady=(0, 20))

        # 4. Zone de Log
        log_frame = ttk.LabelFrame(content_frame, text=" CONSOLE DE SUIVI ", style="Card.TLabelframe", padding="2")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(log_frame, font=("Consolas", 10), bg="#0f172a", fg="#f8fafc", borderwidth=0, padx=10, pady=10)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def setup_jort_tab(self):
        # Contenu
        content_frame = ttk.Frame(self.jort_tab, padding="30", style="Main.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Filtres JORT
        filter_frame = ttk.LabelFrame(content_frame, text=" PARAMÈTRES DE RECHERCHE JORT ", style="Card.TLabelframe", padding="20")
        filter_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Mention d'Autonomie
        autonomy_lbl = ttk.Label(filter_frame, text="🛡️ AUTONOMIE TOTALE : Scraping JORT géré en local (Playwright) pour une indépendance complète des enquêtes.", font=("Segoe UI", 8, "italic"), foreground="#2563eb", background="white")
        autonomy_lbl.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 15))
        
        row = 1
        ttk.Label(filter_frame, text="Mots-clés :", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=8)
        self.ent_jort_kw = ttk.Entry(filter_frame, font=("Segoe UI", 10))
        self.ent_jort_kw.grid(row=row, column=1, columnspan=3, sticky=tk.EW, padx=(15, 0), pady=8)
        filter_frame.columnconfigure(1, weight=1)

        row += 1
        ttk.Label(filter_frame, text="Catégorie :", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=8)
        self.cb_jort_cat = ttk.Combobox(filter_frame, values=[
            "Toutes catégories", "Constitution de sociétés", "Gestion de sociétés", 
            "Convocations", "Actes judiciaires", "Actes administratifs", 
            "Associations, partis, syndicats", "Fonds de commerce"
        ], state="readonly", font=("Segoe UI", 10))
        self.cb_jort_cat.grid(row=row, column=1, columnspan=3, sticky=tk.EW, padx=(15, 0), pady=8)
        self.cb_jort_cat.current(0)

        row += 1
        ttk.Label(filter_frame, text="Année Début :", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=8)
        years = [str(y) for y in range(2025, 2009, -1)]
        self.cb_jort_from = ttk.Combobox(filter_frame, values=years, width=12, state="readonly")
        self.cb_jort_from.grid(row=row, column=1, sticky=tk.W, padx=(15, 0), pady=8)
        self.cb_jort_from.set("2024")

        ttk.Label(filter_frame, text="Année Fin :", style="Card.TLabel").grid(row=row, column=2, sticky=tk.W, padx=(20, 0), pady=8)
        self.cb_jort_to = ttk.Combobox(filter_frame, values=years, width=12, state="readonly")
        self.cb_jort_to.grid(row=row, column=3, sticky=tk.W, padx=(15, 0), pady=8)
        self.cb_jort_to.set("2025")

        row += 1
        ttk.Label(filter_frame, text="Pages max :", style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=8)
        self.ent_jort_pages = ttk.Entry(filter_frame, width=12, font=("Segoe UI", 10))
        self.ent_jort_pages.grid(row=row, column=1, sticky=tk.W, padx=(15, 0), pady=8)
        self.ent_jort_pages.insert(0, "5")

        # 2. Progression & Bouton
        action_frame = ttk.Frame(content_frame, style="Main.TFrame")
        action_frame.pack(fill=tk.X)
        self.jort_progress = ttk.Progressbar(action_frame, orient=tk.HORIZONTAL, mode='determinate', style="Horizontal.TProgressbar")
        self.jort_progress.pack(fill=tk.X, pady=(0, 15))

        self.btn_jort_run = ttk.Button(action_frame, text="🚀 LANCER L'EXTRACTION JORT", style="Action.TButton", command=self.start_jort_thread)
        self.btn_jort_run.pack(fill=tk.X, pady=(0, 20))

        # 3. Zone de Log JORT
        log_frame = ttk.LabelFrame(content_frame, text=" CONSOLE JORT ", style="Card.TLabelframe", padding="2")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.jort_log_area = scrolledtext.ScrolledText(log_frame, font=("Consolas", 10), bg="#0f172a", fg="#f8fafc", borderwidth=0, padx=10, pady=10)
        self.jort_log_area.pack(fill=tk.BOTH, expand=True)

    def setup_settings_tab(self):
        content = ttk.Frame(self.settings_tab, padding="40", style="Main.TFrame")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Info Card
        info_card = ttk.LabelFrame(content, text=" À PROPOS ", style="Card.TLabelframe", padding="20")
        info_card.pack(fill=tk.X, pady=(0, 20))

        info_text = (
            "Ba7ath Edge Pro est un concentrateur d'outils d'extraction locale.\n\n"
            "• Version actuelle : Pro v8.0 (Modern Edition)\n"
            "• Le module TUNEPS est actif et optimisé.\n"
            "• Le module JORT est désormais disponible avec gestion autonome (JortSearch).\n"
        )
        ttk.Label(info_card, text=info_text, justify=tk.LEFT, style="Card.TLabel").pack(anchor=tk.W)
        
        jort_notice = (
            "⚖️ NOTE IMPORTANTE : La seule solution viable pour les données JORT est le site JortSearch.\n"
            "Il est impératif de créer un compte sur https://www.jortsearch.com, de le valider,\n"
            "puis d'utiliser vos identifiants ci-dessous pour activer l'extraction."
        )
        ttk.Label(info_card, text=jort_notice, justify=tk.LEFT, foreground="#ef4444", font=("Segoe UI", 9, "italic"), background="white").pack(anchor=tk.W, pady=(15, 0))

        # SECTION COMPTE JORT (Card)
        st_frame = ttk.LabelFrame(content, text=" ⚖️ GESTION DE COMPTE JORT ", style="Card.TLabelframe", padding="20")
        st_frame.pack(fill=tk.X, pady=10)

        for child in st_frame.winfo_children():
            try: child.configure(background="white")
            except: pass

        # Login part
        ttk.Label(st_frame, text="PARAMÈTRES DE CONNEXION", font=("Segoe UI", 10, "bold"), foreground="#2563eb", background="white").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        ttk.Label(st_frame, text="Email utilisateur :", style="Card.TLabel").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.set_j_user = ttk.Entry(st_frame, width=40)
        self.set_j_user.grid(row=1, column=1, sticky=tk.W, padx=15, pady=5)
        
        ttk.Label(st_frame, text="Mot de passe :", style="Card.TLabel").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.set_j_pass = ttk.Entry(st_frame, width=40, show="*")
        self.set_j_pass.grid(row=2, column=1, sticky=tk.W, padx=15, pady=5)
        
        ttk.Button(st_frame, text="💾 SAUVEGARDER LES IDENTIFIANTS", style="Action.TButton", command=self.save_jort_creds).grid(row=3, column=1, sticky=tk.E, pady=15)

        # Chargement initial des creds
        self.load_jort_creds()

        ttk.Label(content, text=f"Dernière mise à jour système : {datetime.now().strftime('%d/%m/%Y')}", font=("Segoe UI", 8), foreground="#94a3b8").pack(side=tk.BOTTOM, pady=20)

    def log(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{now}] {msg}\n")
        self.log_area.see(tk.END)

    def jort_log(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self.jort_log_area.insert(tk.END, f"[{now}] {msg}\n")
        self.jort_log_area.see(tk.END)

    def save_jort_creds(self):
        u = self.set_j_user.get()
        p = self.set_j_pass.get()
        with open("jort_credentials.json", "w") as f:
            json.dump({"user": u, "pass": p}, f)
        messagebox.showinfo("Ba7ath JORT", "Identifiants JORT sauvegardés.")

    def load_jort_creds(self):
        if os.path.exists("jort_credentials.json"):
            try:
                with open("jort_credentials.json", "r") as f:
                    creds = json.load(f)
                    self.set_j_user.insert(0, creds.get("user", ""))
                    self.set_j_pass.insert(0, creds.get("pass", ""))
            except: pass

    def start_jort_thread(self):
        self.btn_jort_run.config(state=tk.DISABLED)
        self.update_system_status(True) # VOYANT ORANGE
        self.jort_progress["value"] = 0
        self.status_var.set("Scraping JORT en cours...")
        threading.Thread(target=self.run_jort_logic, daemon=True).start()

    def run_jort_logic(self):
        user = self.set_j_user.get()
        pwd = self.set_j_pass.get()
        kw = self.ent_jort_kw.get()
        try:
            pages = int(self.ent_jort_pages.get())
        except: pages = 5

        if not user or not pwd:
            self.jort_log("⚠️ Erreur : Identifiants JORT manquants (Onglet Paramètres).")
            self.btn_jort_run.config(state=tk.NORMAL)
            self.update_system_status(False)
            return

        try:
            logic = JortLogic(self.jort_log)
            y_from = self.cb_jort_from.get()
            y_to = self.cb_jort_to.get()
            cat = self.cb_jort_cat.get()
            
            df = asyncio.run(logic.run_scrape(user, pwd, kw, y_from, y_to, cat, pages))

            if df is not None and not df.empty:
                fname = f"JORT_{kw}_{datetime.now().strftime('%H%M%S')}.xlsx"
                df.to_excel(fname, index=False)
                self.jort_progress["value"] = 100
                self.jort_log(f"✅ EXPORT RÉUSSI : {fname}")
                messagebox.showinfo("Ba7ath JORT", f"Extraction Terminée !\n{len(df)} dossiers exportés.")
            else:
                self.jort_log("❌ Échec ou aucun résultat JORT.")
        except Exception as e:
            self.jort_log(f"❌ Erreur JORT : {e}")
        finally:
            self.btn_jort_run.config(state=tk.NORMAL)
            self.update_system_status(False) # VOYANT VERT
            self.status_var.set("Prêt")

    def _auto_format_date(self, event):
        if event.keysym == 'BackSpace': return
        entry = event.widget
        val = entry.get()
        if len(val) == 2 or len(val) == 5:
            entry.insert(tk.END, '/')

    def _set_date_today(self, entry):
        entry.delete(0, tk.END)
        entry.insert(0, datetime.now().strftime("%d/%m/%Y"))

    def _reset_dates(self):
        self.ent_from.delete(0, tk.END)
        self.ent_from.insert(0, datetime.now().strftime("01/01/%Y"))
        self.ent_to.delete(0, tk.END)
        self.ent_to.insert(0, datetime.now().strftime("%d/%m/%Y"))

    def start_thread(self):
        self.btn_run.config(state=tk.DISABLED)
        self.update_system_status(True) # VOYANT ORANGE
        self.progress["value"] = 0
        self.status_var.set("Scraping TUNEPS en cours...")
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        # Récupération et conversion des dates (JJ/MM/AAAA -> YYYY-MM-DD)
        def convert_date(d):
            try:
                p = d.split('/')
                if len(p) == 3: return f"{p[2]}-{p[1]}-{p[0]}"
                return d
            except: return d

        kw = self.ent_keywords.get()
        lim_str = self.ent_limit.get()
        lim = int(lim_str) if lim_str.isdigit() else 50
        df_from = convert_date(self.ent_from.get())
        df_to = convert_date(self.ent_to.get())
        buyer_name = self.cb_buyer.get()
        buyer_id = self.buyers_data.get(buyer_name, "")
        
        status_map = {"Tous": "", "Attribué": "157", "Infructueux": "158", "Annulé": "156"}
        sme_map = {"Tous": "", "Oui": "1", "Non": "2"}
        
        try:
            logic = TunepsLogic(self.log)
            df = asyncio.run(logic.run_scrape(
                kw, lim, df_from, df_to, 
                status_map[self.cb_status.get()], 
                sme_map[self.cb_sme.get()],
                buyer_id
            ))
            
            if df is not None and not df.empty:
                prefix = kw if kw else "global"
                fname = f"TUNEPS_PRO_{prefix}_{datetime.now().strftime('%H%M%S')}.xlsx"
                df.to_excel(fname, index=False)
                self.progress["value"] = 100
                self.log(f"✅ EXPORT RÉUSSI : {fname}")
                self.status_var.set("Prêt")
                messagebox.showinfo("Ba7ath Pro", f"Extraction Terminée !\n{len(df)} dossiers exportés.")
            else:
                self.log("❌ Échec de l'extraction ou aucun résultat.")
                self.status_var.set("Prêt")
                messagebox.showwarning("Ba7ath Pro", "Aucun résultat trouvé.")
        except Exception as e:
            self.log(f"❌ Erreur TUNEPS : {e}")
        finally:
            self.btn_run.config(state=tk.NORMAL)
            self.update_system_status(False) # VOYANT VERT

if __name__ == "__main__":
    root = tk.Tk()
    
    # Icône Ba7ath
    try:
        icon_path = resource_path("ba7ath.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except: pass
    
    app = TunepsApp(root)
    root.mainloop()
