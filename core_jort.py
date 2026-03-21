import asyncio
import pandas as pd
import re
import streamlit as st
from datetime import datetime
from playwright.async_api import async_playwright

class JORTScraper:
    """Moteur de scraping JORT optimisé pour Vaadin / Shadow DOM (v2026)."""
    
    def __init__(self, user, pwd, headless=True):
        self.user = user
        self.pwd = pwd
        self.headless = headless
        self.base_url = "https://www.jortsearch.com"
        self.browser_args = ["--disable-blink-features=AutomationControlled"]
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

    async def run(self, keyword, max_safety_pages=50, year_range=None):
        """Exécute l'extraction par sessions ultra-isolées (Année -> Catégorie)."""
        # 1. Détection initiale des années
        years = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless, args=self.browser_args)
            page = await browser.new_page()
            try:
                if await self._login(page) and await self._do_search(page, keyword):
                    years = await self._get_year_filters(page)
            except Exception as e:
                st.error(f"Erreur détection années : {e}")
            finally:
                await browser.close()

        if year_range and years:
            y_min, y_max = year_range
            years = [y for y in years if y_min <= int(y) <= y_max]

        if not years:
            st.warning("⚠️ Aucune année trouvée.")
            return pd.DataFrame()

        st.info(f"🚀 Lancement de l'extraction ultra-robuste (Isolation Catégorielle) pour {len(years)} segments.")
        all_data = []
        seen_ids = set() # Pour éviter les doublons entre Direct et Catégories

        def add_unique(data_list):
            for d in data_list:
                # Signature unique basée sur le contenu partiel
                sig = hash(d["Contenu"][:100] + d["Catégorie"] + d["Journal"])
                if sig not in seen_ids:
                    seen_ids.add(sig)
                    all_data.append(d)

        for year in years:
            # A. Phase Directe (capturer les orphelins et les petits segments)
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless, args=self.browser_args)
                page = await browser.new_page()
                try:
                    if await self._login(page) and await self._do_search(page, keyword):
                        if await self._apply_year_filter(page, year):
                            year_total, _ = await self._get_pagination_info(page)
                            
                            if year_total <= 110:
                                # Année légère : On prend tout ici
                                p_data = await self._scrape_complete_segment(page, year, "Direct", max_safety_pages)
                                add_unique(p_data)
                            else:
                                # Année lourde : On prend ce qu'on peut en direct (les 110 premières + Orphelins)
                                st.write(f"📂 {year} est volumineux ({year_total} annonces). Extraction des 110 premières...")
                                p_data = await self._scrape_complete_segment(page, year, "Direct (Partiel)", max_safety_pages)
                                add_unique(p_data)
                                
                                # Puis on boucle sur les catégories pour le reste
                                categories = await self._get_category_filters(page)
                                await browser.close() # On ferme pour libérer de la RAM
                                
                                for cat in categories:
                                    # NOUVELLE SESSION PAR CATÉGORIE
                                    async with async_playwright() as p_cat:
                                        b_cat = await p_cat.chromium.launch(headless=self.headless, args=self.browser_args)
                                        p_cat_obj = await b_cat.new_page()
                                        try:
                                            if await self._login(p_cat_obj) and await self._do_search(p_cat_obj, keyword):
                                                if await self._apply_year_filter(p_cat_obj, year):
                                                    if await self._apply_category_filter(p_cat_obj, cat):
                                                        c_data = await self._scrape_complete_segment(p_cat_obj, year, cat, max_safety_pages)
                                                        add_unique(c_data)
                                        finally:
                                            await b_cat.close()
                except Exception as e:
                    st.error(f"Erreur segment {year} : {e}")
                finally:
                    if not browser.is_connected(): pass # Déjà fermé
                    else: await browser.close()
        
        return pd.DataFrame(all_data)

    async def _scrape_complete_segment(self, page, year, name, max_pages):
        """Extrait toutes les pages disponibles pour un filtre actif."""
        _, total_pages = await self._get_pagination_info(page)
        pages_to_do = min(total_pages, max_pages)
        st.write(f"⏳ **{year}** / **{name}** : Extraction...")
        
        results = []
        for p_idx in range(pages_to_do):
            p_data = await self._scrape_page(page)
            results.extend(p_data)
            if p_idx < pages_to_do - 1:
                if not await self._goto_next_page(page): break
        
        if results:
            st.write(f"✅ +{len(results)} trouvées dans ce segment.")
        return results

    async def _login(self, page):
        """Connexion standard avec délai Cloud."""
        try:
            await page.goto(f"{self.base_url}/login", wait_until="networkidle", timeout=60000)
            # Laisser le temps à Vaadin (Java) d'hydrater la page JS
            await page.locator("vaadin-text-field input").first.wait_for(state="visible", timeout=30000)
            await asyncio.sleep(2) 
            await page.locator("vaadin-text-field input").first.fill(self.user)
            await page.locator("vaadin-password-field input").first.fill(self.pwd)
            await page.click("vaadin-button[theme~='primary']")
            # 45 secondes de marge pour le cloud au lieu de 15 !
            await page.wait_for_function("() => !window.location.href.includes('/login')", timeout=45000)
            return True
        except Exception as e:
            st.error(f"Échec Login : {e}")
            try:
                await page.screenshot(path="debug_login.png")
                st.image("debug_login.png", caption="Écran au moment de l'erreur Login")
            except: pass
            return False

    async def _do_search(self, page, keyword):
        """Recherche textuelle avec délai Cloud."""
        try:
            if "/search" not in page.url:
                await page.goto(f"{self.base_url}/search", wait_until="networkidle", timeout=60000)
            await page.locator("vaadin-text-field input").first.wait_for(state="visible", timeout=30000)
            await asyncio.sleep(2)
            await page.locator("vaadin-text-field input").first.fill(keyword)
            # Bouton loupe
            btn = page.locator("vaadin-button").filter(has=page.locator("iron-icon[icon='vaadin:search']")).first
            if await btn.count() == 0: btn = page.locator("vaadin-button:has-text('Rechercher')")
            await btn.click()
            await page.wait_for_timeout(3000)
            await page.locator("announcement-card").first.wait_for(timeout=45000)
            return True
        except Exception as e:
            st.error(f"Échec Recherche : {e}")
            try:
                await page.screenshot(path="debug_search.png")
                st.image("debug_search.png", caption="Écran au moment de l'erreur Recherche")
            except: pass
            return False

    async def _get_year_filters(self, page):
        """Boutons d'année dans la sidebar."""
        try:
            sidebar = page.locator("vaadin-vertical-layout").filter(has_text="Filtrer par année").first
            await sidebar.wait_for(timeout=10000)
            # Scroll pour voir tout
            for _ in range(3):
                await sidebar.evaluate("el => el.scrollTop += 500")
                await asyncio.sleep(0.3)
            
            all_btns = await page.locator("vaadin-button").all_inner_texts()
            years = [t.strip() for t in all_btns if re.match(r"^(19|20)\d{2}$", t.strip())]
            return sorted(list(set(years)), reverse=True)
        except Exception as e:
            st.error(f"Échec Filtres Année : {e}")
            try:
                await page.screenshot(path="debug_filters.png")
                st.image("debug_filters.png", caption="Écran au moment de l'erreur Filtres")
            except: pass
            return []

    async def _apply_year_filter(self, page, year):
        """Filtre année."""
        try:
            await page.locator("vaadin-button").filter(has_text=year).first.click()
            await page.wait_for_timeout(2000)
            await page.wait_for_selector("vaadin-button:has-text('Annuler')", timeout=10000)
            return True
        except: return False

    async def _get_category_filters(self, page):
        """Filtres catégories."""
        try:
            section = page.locator("vaadin-vertical-layout").filter(has_text="Filtrer par catégorie")
            if await section.count() == 0: return []
            btns = await section.locator("vaadin-button").all_inner_texts()
            cats = [t.strip() for t in btns if not re.match(r"^\d{4}$", t.strip()) and len(t.strip()) > 3 and "Annuler" not in t]
            return list(dict.fromkeys(cats))
        except: return []

    async def _apply_category_filter(self, page, cat):
        """Filtre catégorie."""
        try:
            await page.locator("vaadin-button").filter(has_text=cat).first.click()
            await page.wait_for_timeout(2000)
            return True
        except: return False

    async def _get_pagination_info(self, page):
        """Récupère 'X / Y'."""
        try:
            await asyncio.sleep(1) # Laisse le temps à l'UI de switch
            label = page.locator("vaadin-horizontal-layout label").filter(has_text="/").first
            text = await label.inner_text()
            total = int(re.sub(r"\D", "", text.split("/")[1]))
            return total * 10, total
        except: return 0, 1

    async def _scrape_page(self, page):
        """Extrait les cartes."""
        cards = await page.locator("announcement-card").all()
        data = []
        for c in cards:
            try:
                t = await c.evaluate("node => node.title")
                st_ = await c.evaluate("node => node.subTitle")
                cnt = await c.locator("span").first.inner_text()
                data.append({"Journal": t, "Catégorie": st_, "Contenu": cnt, "Extraction": datetime.now().strftime("%Y-%m-%d %H:%M")})
            except: pass
        return data

    async def _goto_next_page(self, page):
        """Bouton Suivant."""
        try:
            btn = page.locator("vaadin-horizontal-layout").filter(has=page.locator("label:has-text('/')")).locator("vaadin-button").last
            if await btn.is_enabled():
                old_id = await page.locator("announcement-card").first.inner_text()
                await btn.click()
                for _ in range(15):
                    await asyncio.sleep(0.7)
                    cards = await page.locator("announcement-card").all()
                    if cards and await cards[0].inner_text() != old_id: return True
        except: pass
        return False
