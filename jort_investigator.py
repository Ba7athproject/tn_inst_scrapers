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

    async def login(self, page):
        """Gère l'authentification sur le portail Vaadin."""
        print("Connexion au compte JORT...")
        await page.goto(f"{self.base_url}/login")
        
        # On attend les champs de saisie (Vaadin utilise souvent des tags personnalisés)
        await page.wait_for_selector("vaadin-text-field[name='username'], input[type='text']")
        
        # Saisie des identifiants
        await page.fill("input[name='username']", self.username)
        await page.fill("input[name='password']", self.password)
        
        # Clic sur le bouton de connexion
        await page.click("vaadin-button[theme~='primary']")
        
        # Attendre que la redirection vers la recherche soit effective
        await page.wait_for_url(f"{self.base_url}/search**")
        print("Connecté avec succès.")

    async def extract_page_data(self, page):
        """Extrait les annonces de la page actuelle."""
        results = []
        await page.wait_for_selector("announcement-card", timeout=10000)
        cards = await page.locator("announcement-card").all()
        
        for card in cards:
            title = await card.get_attribute("title") or ""
            subtitle = await card.get_attribute("subtitle") or ""
            content = await card.locator("span").inner_text()
            
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
            try:
                await self.login(page)
            except Exception as e:
                print(f"Échec de connexion : {e}")
                await browser.close()
                return pd.DataFrame()

            # 2. Recherche
            await page.goto(f"{self.base_url}/search/{keyword}")
            
            all_data = []
            current_page = 1
            
            while current_page <= max_pages:
                print(f"Traitement page {current_page}...")
                data = await self.extract_page_data(page)
                all_data.extend(data)
                
                # 3. Pagination
                next_button = page.locator("vaadin-button:has(iron-icon[icon='vaadin:arrow-right'])")
                if await next_button.is_visible() and await next_button.is_enabled():
                    old_text = await page.locator("announcement-card").first.inner_text()
                    await next_button.click()
                    current_page += 1
                    # Attendre que le contenu de la page change
                    await page.wait_for_function(
                        f"document.querySelector('announcement-card').innerText !== `{old_text}`"
                    )
                else:
                    break
            
            await browser.close()
            return pd.DataFrame(all_data)