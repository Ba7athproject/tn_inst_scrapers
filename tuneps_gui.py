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

# --- INTERFACE GUI PROFESSIONNELLE ---

class TunepsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ba7ath Edge Scraper Pro v7.4")
        self.root.geometry("900x800")
        self.root.configure(bg="#f0f2f5")
        
        self.buyers_data = load_buyers()
        self.buyer_names = sorted(list(self.buyers_data.keys()))

        # Configuration des Styles
        self.setup_styles()

        # Conteneur Principal
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Onglet TUNEPS
        self.tuneps_tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(self.tuneps_tab, text=" 🏛️ TUNEPS ")
        self.setup_tuneps_tab()

        # Onglet Paramètres (Placeholder)
        self.settings_tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(self.settings_tab, text=" ⚙️ Paramètres ")
        self.setup_settings_tab()

        # Barre d'état
        self.status_var = tk.StringVar(value="Prêt")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Couleurs
        bg_color = "#f0f2f5"
        accent_color = "#2e7d32"
        secondary_color = "#2c3e50"
        
        style.configure("Main.TFrame", background=bg_color)
        style.configure("TNotebook", background=bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", padding=[15, 5], font=("Segoe UI", 10))
        
        style.configure("TLabel", background=bg_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=bg_color, font=("Segoe UI", 18, "bold"), foreground=accent_color)
        
        style.configure("TLabelframe", background=bg_color, font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background=bg_color, foreground=secondary_color)
        
        style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), padding=10)
        style.configure("Horizontal.TProgressbar", thickness=15)

    def setup_tuneps_tab(self):
        # Header
        header_frame = ttk.Frame(self.tuneps_tab, style="Main.TFrame")
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        ttk.Label(header_frame, text="🏛️ TUNEPS Edge Scraper Pro", style="Header.TLabel").pack(side=tk.LEFT)

        # Contenu
        content_frame = ttk.Frame(self.tuneps_tab, padding="20", style="Main.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Filtres Principaux
        filter_frame = ttk.LabelFrame(content_frame, text=" CONFIGURATION DE RECHERCHE ", padding="15")
        filter_frame.pack(fill=tk.X, pady=(0, 20))

        # Layout Grille pour filtres
        row = 0
        ttk.Label(filter_frame, text="Mots-clés :").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.ent_keywords = ttk.Entry(filter_frame, font=("Segoe UI", 10))
        self.ent_keywords.grid(row=row, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        filter_frame.columnconfigure(1, weight=1)

        row += 1
        ttk.Label(filter_frame, text="Acheteur Public :").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cb_buyer = ttk.Combobox(filter_frame, values=["Tous"] + self.buyer_names, font=("Segoe UI", 10))
        self.cb_buyer.grid(row=row, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        self.cb_buyer.set("Tous")

        row += 1
        ttk.Label(filter_frame, text="Limite :").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.ent_limit = ttk.Entry(filter_frame, width=10, font=("Segoe UI", 10))
        self.ent_limit.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.ent_limit.insert(0, "50")

        # 2. Options Avancées
        adv_frame = ttk.Frame(content_frame, style="Main.TFrame")
        adv_frame.pack(fill=tk.X, pady=(0, 20))

        # Dates
        date_frame = ttk.LabelFrame(adv_frame, text=" PÉRIODE (Format: JJ/MM/AAAA) ", padding="10")
        date_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(date_frame, text="Du :").grid(row=0, column=0, padx=5)
        self.ent_from = ttk.Entry(date_frame, width=12)
        self.ent_from.grid(row=0, column=1, padx=5)
        self.ent_from.insert(0, datetime.now().strftime("01/01/%Y"))
        self.ent_from.bind("<KeyRelease>", self._auto_format_date)
        
        ttk.Label(date_frame, text="Au :").grid(row=0, column=2, padx=5)
        self.ent_to = ttk.Entry(date_frame, width=12)
        self.ent_to.grid(row=0, column=3, padx=5)
        self.ent_to.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ent_to.bind("<KeyRelease>", self._auto_format_date)

        # Boutons rapides dates
        btn_frame = ttk.Frame(date_frame, style="Main.TFrame")
        btn_frame.grid(row=1, column=0, columnspan=4, pady=(5, 0))
        ttk.Button(btn_frame, text="Aujourd'hui", width=12, command=lambda: self._set_date_today(self.ent_to)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Reset", width=10, command=self._reset_dates).pack(side=tk.LEFT, padx=2)

        # Statut & PME
        status_frame = ttk.LabelFrame(adv_frame, text=" FILTRES ", padding="10")
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(status_frame, text="Statut :").grid(row=0, column=0, padx=5)
        self.cb_status = ttk.Combobox(status_frame, values=["Tous", "Attribué", "Infructueux", "Annulé"], state="readonly", width=12)
        self.cb_status.current(1) # Défaut: Attribué
        self.cb_status.grid(row=0, column=1, padx=5)
        ttk.Label(status_frame, text="PME :").grid(row=0, column=2, padx=5)
        self.cb_sme = ttk.Combobox(status_frame, values=["Tous", "Oui", "Non"], state="readonly", width=8)
        self.cb_sme.current(0)
        self.cb_sme.grid(row=0, column=3, padx=5)

        # 3. Barre de Progression
        self.progress = ttk.Progressbar(content_frame, orient=tk.HORIZONTAL, mode='determinate', style="Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # 4. Bouton Principal
        self.btn_run = ttk.Button(content_frame, text="🚀 LANCER L'EXTRACTION TUNEPS", style="Action.TButton", command=self.start_thread)
        self.btn_run.pack(fill=tk.X, pady=(0, 20))

        # 5. Zone de Log
        log_frame = ttk.LabelFrame(content_frame, text=" CONSOLE DE SUIVI ", padding="2")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(log_frame, font=("Consolas", 9), bg="#1e272e", fg="#ffffff", borderwidth=0)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def setup_settings_tab(self):
        content = ttk.Frame(self.settings_tab, padding="40", style="Main.TFrame")
        content.pack(fill=tk.BOTH, expand=True)
        ttk.Label(content, text="⚙️ Paramètres de l'Application", font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))
        
        info_text = (
            "Ba7ath Edge Scraper est un concentrateur d'outils d'extraction locale.\n\n"
            "• Version actuelle : Pro v7.4.2\n"
            "• Le module TUNEPS est actif et optimisé.\n"
            "• D'autres modules de scraping seront intégrés dans les versions futures.\n"
        )
        ttk.Label(content, text=info_text, justify=tk.LEFT).pack()
        
        ttk.Separator(content, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=30)
        ttk.Label(content, text=f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y')}").pack()

    def log(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{now}] {msg}\n")
        self.log_area.see(tk.END)

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
        self.progress["value"] = 0
        self.status_var.set("Scraping en cours...")
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
        
        logic = TunepsLogic(self.log)
        
        # Injection d'un callback de progression (via le log callback mais plus riche)
        # Pour une vraie barre de progression, on pourrait passer un callback spécifique.
        # Ici on va simuler ou mapper les logs.
        
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
            self.status_var.set("Extraction terminée avec succès")
            messagebox.showinfo("Ba7ath Pro", f"Extraction Terminée !\n{len(df)} dossiers exportés dans :\n{fname}")
        else:
            self.log("❌ Échec de l'extraction ou aucun résultat.")
            self.status_var.set("Aucun résultat trouvé")
            messagebox.showwarning("Ba7ath Pro", "Aucun résultat trouvé.")
        
        self.btn_run.config(state=tk.NORMAL)

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
