import asyncio
import re
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

class JORTScraper:
    def __init__(self, username, password, headless=True):
        self.base_url = "https://www.jortsearch.com"
        self.username = username
        self.password = password
        self.headless = headless

    def log(self, message, logger=None):
        """Affiche le message dans la console et envoie au logger si présent."""
        print(message)
        if logger:
            try: logger(message)
            except: pass

    async def login(self, page, logger=None):
        """Connexion standard avec gestion Vaadin / Shadow DOM."""
        self.log("Connexion au compte JORT...", logger)
        try:
            await page.goto(f"{self.base_url}/login", wait_until="networkidle", timeout=60000)
            await page.wait_for_selector("vaadin-text-field", timeout=20000)
            
            # Attente de l'input dans le composant Vaadin
            await page.locator('vaadin-text-field:has(label:has-text("Email")), vaadin-email-field, vaadin-text-field').locator("input").first.fill(self.username)
            await page.locator('vaadin-password-field input').first.fill(self.password)
            
            # Clic sur le bouton de connexion
            await page.click("vaadin-button[theme~='primary'], vaadin-button:has-text('Connexion')")
            
            # Attendre que la redirection soit effective
            await page.wait_for_function("() => !window.location.href.includes('/login')", timeout=45000)
            self.log("Connecté avec succès.", logger)
            return True
        except Exception as e:
            self.log(f"Échec de connexion : {e}", logger)
            return False

    async def signup(self, page, first_name, last_name, email, password):
        """Gère l'auto-inscription sur jortsearch.com."""
        print(f"Tentative d'inscription pour {email}...")
        try:
            await page.goto(f"{self.base_url}/signup", wait_until="networkidle", timeout=60000)
            await page.wait_for_selector("vaadin-text-field", timeout=20000)
            
            # Attente et remplissage des champs (Sélecteurs ultra-précis basés sur les rôles suggérés par Playwright)
            import re
            await page.get_by_role("textbox", name=re.compile(r"Prénom", re.I)).fill(first_name)
            await page.get_by_role("textbox", name=re.compile(r"^Nom", re.I)).fill(last_name)
            await page.get_by_role("textbox", name=re.compile(r"E-mail", re.I)).fill(email)
            await page.get_by_role("textbox", name=re.compile(r"Mot de passe", re.I), exact=True).fill(password)
            await page.get_by_role("textbox", name=re.compile(r"Confirmer", re.I)).fill(password)
            
            # Cocher la case CGU (Sélecteur direct sur le composant)
            checkbox = page.locator("vaadin-checkbox")
            if await checkbox.count() > 0:
                await checkbox.first.click()
            
            # Bouton S'inscrire (Sélecteur par texte)
            await page.click('vaadin-button:has-text("Inscription")')
            
            # Attendre confirmation ou redirection
            await asyncio.sleep(5)
            if "login" in page.url or "confirm" in page.url:
                print("Inscription envoyée avec succès. Veuillez vérifier vos e-mails.")
                return True
            
            # Vérifier si un message d'erreur est apparu
            error_msg = await page.locator(".error-message, [theme~='error']").first.text_content() if await page.locator(".error-message, [theme~='error']").count() > 0 else "Inconnu"
            print(f"Échec Inscription (Site) : {error_msg}")
            return False
        except Exception as e:
            print(f"Échec Inscription (Script) : {e}")
            return False

    async def extract_page_data(self, page):
        """Extrait les annonces de la page actuelle avec accès aux propriétés Shadow DOM."""
        results = []
        try:
            await page.wait_for_selector("announcement-card", timeout=10000)
        except:
            return results
            
        cards = await page.locator("announcement-card").all()
        
        for card in cards:
            # On utilise evaluate car title/subTitle sont souvent des propriétés JS dans Vaadin
            title = await card.evaluate("node => node.title") or ""
            subtitle = await card.evaluate("node => node.subTitle") or ""
            content = await card.locator("span").first.inner_text()
            
            # Extraction de l'identifiant légal (ex: 2025R00472SODB1)
            jort_id = ""
            match = re.search(r'(\d{4}[A-Z]\d{5}[A-Z]{4}\d)', content)
            if match: jort_id = match.group(1)

            results.append({
                "Journal": title,
                "Categorie": subtitle,
                "Contenu": content,
                "ID_Legal": jort_id,
                "Extraction": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        return results

    async def search_and_scrape(self, keyword, max_pages=5):
        async with async_playwright() as p:
            # Lancement avec un user-agent pour éviter d'être bloqué
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # 1. Login
            if not await self.login(page):
                await browser.close()
                return pd.DataFrame()

            # 2. Recherche
            print(f"Recherche du mot-clé : {keyword}...")
            await page.goto(f"{self.base_url}/search", wait_until="networkidle")
            search_input = page.locator("vaadin-text-field input").first
            await search_input.wait_for(state="visible")
            await search_input.fill(keyword)
            
            # Clic sur le bouton loupe
            search_btn = page.locator("vaadin-button").filter(has=page.locator("iron-icon[icon='vaadin:search']")).first
            if await search_btn.count() == 0:
                search_btn = page.locator("vaadin-button:has-text('Rechercher')")
            await search_btn.click()
            
            # Attendre les résultats
            try:
                await page.locator("announcement-card").first.wait_for(timeout=20000)
            except:
                print("Aucun résultat trouvé.")
                await browser.close()
                return pd.DataFrame()
            
            all_data = []
            current_page = 1
            
            while current_page <= max_pages:
                print(f"Traitement page {current_page}...")
                data = await self.extract_page_data(page)
                all_data.extend(data)
                
                # 3. Pagination (Bouton Suivant plus robuste)
                next_button = page.locator("vaadin-horizontal-layout").filter(has=page.locator("label:has-text('/')")).locator("vaadin-button").last
                
                if await next_button.is_visible() and await next_button.is_enabled():
                    old_id = await page.locator("announcement-card").first.inner_text()
                    await next_button.click()
                    current_page += 1
                    
                    # Attendre que le contenu change (ID de la 1ère carte)
                    content_changed = False
                    for _ in range(10):
                        await asyncio.sleep(1)
                        cards = await page.locator("announcement-card").all()
                        if cards and await cards[0].inner_text() != old_id:
                            content_changed = True
                            break
                    if not content_changed:
                        break
                else:
                    break
            
            await browser.close()
            return pd.DataFrame(all_data)

    async def run_scrape(self, user, pwd, keywords, year_start=None, year_end=None, category=None, max_pages=5, logger=None):
        """Lance le scraping complet avec filtres temporels et thématiques."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            if not await self.login(page, logger=logger):
                await browser.close()
                return None
            
            all_data = []
            
            # Définition de la plage d'années
            years = []
            if year_start and year_end:
                try:
                    years = list(range(int(year_start), int(year_end) + 1))
                    years.sort(reverse=True) # Du plus récent au plus ancien
                except: pass
            elif year_start:
                years = [year_start]
            
            if not years:
                # Si aucune année, on fait une recherche globale (comportement par défaut)
                years = [None]

            for year in years:
                msg = f"🔍 Scraping JORT - {year if year else 'Indéterminé'} - '{keywords}'"
                self.log(msg, logger)
                
                # 1. Sélectionner l'année si spécifiée
                if year:
                    try:
                        year_btn = page.locator(f".left-bar vaadin-button:has-text('{year}')")
                        if await year_btn.count() > 0:
                            await year_btn.first.click()
                            await page.wait_for_load_state("networkidle")
                    except Exception as e:
                        self.log(f"⚠️ Année {year} indisponible.", logger)

                # 2. Sélectionner la catégorie si spécifiée
                if category and category != "Toutes catégories":
                    try:
                        cat_btn = page.locator(f".left-bar vaadin-button:has-text('{category}')")
                        if await cat_btn.count() > 0:
                            await cat_btn.first.click()
                            await page.wait_for_load_state("networkidle")
                    except Exception as e:
                        self.log(f"⚠️ Catégorie '{category}' non trouvée.", logger)

                # 3. Appliquer les mots-clés
                if keywords:
                    try:
                        search_input = page.locator("input[placeholder*='Que recherchez-vous'], vaadin-text-field input").first
                        await search_input.fill(keywords)
                        await page.keyboard.press("Enter")
                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(2)
                    except Exception as e:
                        self.log(f"⚠️ Erreur saisie : {e}", logger)

                # 4. Extraire les données sur X pages
                for p_idx in range(max_pages):
                    self.log(f"📄 Extraction Page {p_idx + 1}...", logger)
                    page_results = await self.extract_page_data(page)
                    all_data.extend(page_results)
                    
                    # Pagination robuste
                    next_btn = page.locator("vaadin-button:has(iron-icon[icon*='right']), vaadin-button:has(vaadin-icon[icon*='right'])").last
                    
                    if await next_btn.is_visible() and await next_btn.is_enabled():
                        old_first_id = ""
                        try:
                            cards = await page.locator("announcement-card").all()
                            if cards: old_first_id = await cards[0].inner_text()
                        except: pass
                        
                        await next_btn.click()
                        await asyncio.sleep(3)
                        
                        try:
                            new_cards = await page.locator("announcement-card").all()
                            if not new_cards or (old_first_id and await new_cards[0].inner_text() == old_first_id):
                                break
                        except: break
                    else:
                        break
            
            await browser.close()
            return pd.DataFrame(all_data) if all_data else pd.DataFrame()

if __name__ == "__main__":
    # Exemple d'utilisation
    async def main():
        scraper = JORTScraper(username="VOTRE_EMAIL", password="VOTRE_PASSWORD", headless=False)
        df = await scraper.search_and_scrape("Tunisie", max_pages=2)
        print(f"Extraction terminée : {len(df)} résultats trouvés.")
        print(df.head())

    # asyncio.run(main())