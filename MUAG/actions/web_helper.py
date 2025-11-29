"""
WebHelper - Support Playwright Avancé pour CUA Agent
Capacités: Shadow DOM, iframes, matching intelligent, popup handling, fallback Vision
"""
import time
import logging
import threading
from typing import Optional, Dict, List, Tuple
from playwright.sync_api import sync_playwright, Page, ElementHandle, TimeoutError as PlaywrightTimeout

logging.basicConfig(level=logging.INFO)

class WebHelper:
    """
    Helper Playwright avec capacités avancées:
    - Connexion CDP au Chrome existant (port 9222)
    - Shadow DOM piercing
    - Détection dans iframes
    - Matching intelligent multi-stratégies avec scoring
    - Gestion robuste des popups/cookies
    - Fallback intelligent si échec -> retourne False pour déclencher Vision
    """
    
    def __init__(self, debug_port=9222, max_retries=5, retry_delay=2):
        """
        Se connecte à Chrome via CDP avec retry logic
        
        Args:
            debug_port: Port du remote debugging de Chrome
            max_retries: Nombre de tentatives de connexion
            retry_delay: Délai entre chaque tentative (secondes)
        """
        self.debug_port = debug_port
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        self.connected = False
        
        # ✅ Retry logic robuste
        for attempt in range(max_retries):
            try:
                print(f"[WebHelper] Tentative connexion {attempt+1}/{max_retries} sur port {debug_port}...")
                
                self.playwright = sync_playwright().start()
                
                # Connexion à Chrome existant via CDP
                self.browser = self.playwright.chromium.connect_over_cdp(
                    f"http://localhost:{debug_port}"  # localhost, PAS ::1
                )
                
                # Récupérer la page active
                if self.browser.contexts:
                    self.context = self.browser.contexts[0]
                    if self.context.pages:
                        self.page = self.context.pages[0]
                        print(f"[WebHelper] Page active: {self.page.url}")
                    else:
                        print(f"[WebHelper] ⚠️ Aucune page dans le contexte")
                        self.page = None
                else:
                    print(f"[WebHelper] ⚠️ Aucun contexte browser")

                self.connected = True if self.page else False
                print(f"[WebHelper] {'✅ Connecté' if self.connected else '❌ Pas de page'} à Chrome via CDP")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"[WebHelper] ⚠️ Échec: {e}")
                    print(f"[WebHelper] Retry dans {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"[WebHelper] ❌ Impossible de connecter après {max_retries} tentatives")
                    print(f"[WebHelper] Mode Vision seule: {e}")
                    self.connected = False
    
    def refresh_connection(self):
        """Rafraîchir pour obtenir la page active actuelle"""
        if not self.connected:
            return False
        try:
            contexts = self.browser.contexts
            if contexts and contexts[0].pages:
                # Dernière page = page active
                self.page = contexts[0].pages[-1]
                return True
        except:
            self.connected = False
        return False
    
    # ========== EXTRACTION TEXTE ENRICHIE ==========
    
    def get_full_text(self, element: ElementHandle) -> str:
        """
        Extrait TOUT le texte, même fragmenté dans les enfants.
        Critique pour boutons type Amazon où texte est en plusieurs <span>
        """
        try:
            # Pour les inputs, utiliser value
            tag = element.evaluate('el => el.tagName.toLowerCase()')
            if tag == 'input':
                value = element.get_attribute('value') or ""
                if value:
                    return value.strip()[:200]
            
            # Texte direct
            text = element.text_content().strip() if element.text_content() else ""
            
            # Si trop court/vide, chercher dans enfants
            if len(text) < 3:
                try:
                    child_texts = element.evaluate('''el => {
                        const texts = [];
                        const children = el.querySelectorAll('*');
                        for (let i = 0; i < children.length && i < 10; i++) {
                            const txt = children[i].textContent?.trim();
                            if (txt && txt.length > 0 && txt.length < 100) {
                                texts.push(txt);
                            }
                        }
                        return [...new Set(texts)].join(' ');
                    }''')
                    if child_texts and len(child_texts) > len(text):
                        text = child_texts
                except:
                    pass
            
            return text[:200]
        except:
            return ""
    
    # ========== SCAN PAGE AVANCÉ ==========
    
    def scan_page_advanced(self) -> List[Dict]:
        """
        Scan complet de la page:
        - Clickables (buttons, links, div[role='button'])
        - Inputs (input, textarea, contenteditable, iframes)
        - Détection Shadow DOM
        - Retourne format compatible pour matching intelligent
        """
        if not self.connected or not self.page:
            return []
        
        results = []
        time.sleep(0.3)  # Stabilisation DOM
        
        # 1. CLICKABLES (boutons, liens, etc.)
        clickables = self.page.query_selector_all(
            "button, a[href], input[type=button], input[type=submit], "
            "div[role='button'], span[role='button'], "
            "tr[role='row'][tabindex], div[role='listitem']"
        )
        
        for element in clickables:
            try:
                if not element.is_visible():
                    continue
                    
                bbox = element.bounding_box()
                if not bbox or bbox.get('width', 0) == 0:
                    continue
                
                text_content = self.get_full_text(element)
                
                results.append({
                    "type": "clickable",
                    "html_tag": element.evaluate('el => el.tagName.toLowerCase()'),
                    "text": text_content,
                    "coords": bbox,
                    "element": element,
                    "aria": element.get_attribute("aria-label") or "",
                    "title": element.get_attribute("title") or "",
                    "id": element.get_attribute("id") or "",
                    "name": element.get_attribute("name") or "",
                    "class": element.get_attribute("class") or "",
                })
            except:
                pass
        
        # 2. INPUTS CLASSIQUES
        inputs = self.page.query_selector_all(
            "input[type=text], input[type=search], input[type=password], "
            "input:not([type]), textarea, input[name=q], input[name=search], "
            "div[contenteditable='true'], [role='textbox']"
        )
        
        classic_inputs_found = []
        for element in inputs:
            try:
                if not element.is_visible():
                    continue
                    
                bbox = element.bounding_box()
                if not bbox or bbox.get('width', 0) == 0:
                    continue
                
                results.append({
                    "type": "input",
                    "html_tag": element.evaluate('el => el.tagName.toLowerCase()'),
                    "placeholder": element.get_attribute('placeholder') or "",
                    "aria": element.get_attribute('aria-label') or "",
                    "name": element.get_attribute('name') or "",
                    "id": element.get_attribute('id') or "",
                    "title": element.get_attribute('title') or "",
                    "role": element.get_attribute('role') or "",
                    "text": element.text_content().strip() if element.text_content() else "",
                    "coords": bbox,
                    "element": element
                })
                classic_inputs_found.append(element)
            except:
                pass
        
        # 3. DÉTECTION ÉTENDUE si peu d'inputs trouvés
        if len(classic_inputs_found) <= 2:
            logging.info("[WebHelper] Détection étendue: iframes + sélecteurs avancés")
            
            # 3a. Chercher dans iframes
            frames = self.page.frames
            for frame in frames:
                try:
                    if frame != self.page.main_frame:
                        frame_inputs = frame.query_selector_all(
                            "input, textarea, div[contenteditable='true'], [role='textbox']"
                        )
                        for element in frame_inputs:
                            try:
                                bbox = element.bounding_box()
                                if bbox and bbox.get('width', 0) > 0:
                                    results.append({
                                        "type": "input",
                                        "html_tag": element.evaluate('el => el.tagName.toLowerCase()'),
                                        "placeholder": element.get_attribute('placeholder') or "",
                                        "aria": element.get_attribute('aria-label') or "",
                                        "name": element.get_attribute('name') or "",
                                        "id": element.get_attribute('id') or "",
                                        "coords": bbox,
                                        "element": element,
                                        "detection_method": "iframe"
                                    })
                            except:
                                pass
                except:
                    pass
            
            # 3b. Sélecteurs étendus (apps modernes)
            extended_selectors = [
                "input[type='email']", "[contenteditable='true']",
                "[data-testid*='input']", "[data-testid*='field']",
                ".input", ".text-input", ".form-control",
                "div[class*='input']", "div[class*='Input']"
            ]
            
            for selector in extended_selectors:
                try:
                    for element in self.page.query_selector_all(selector):
                        try:
                            bbox = element.bounding_box()
                            if not bbox or bbox.get('width', 0) == 0:
                                continue
                            
                            # Vérifier si déjà présent
                            is_duplicate = any(r["element"] == element for r in results)
                            if not is_duplicate:
                                results.append({
                                    "type": "input",
                                    "html_tag": element.evaluate('el => el.tagName.toLowerCase()'),
                                    "placeholder": element.get_attribute('placeholder') or "",
                                    "aria": element.get_attribute('aria-label') or "",
                                    "name": element.get_attribute('name') or "",
                                    "coords": bbox,
                                    "element": element,
                                    "detection_method": "extended"
                                })
                        except:
                            pass
                except:
                    pass
        
        return results
    
    # ========== MATCHING INTELLIGENT ==========
    
    def find_element_smart(self, description: str, prefer_type: str = None) -> Optional[Tuple[ElementHandle, int]]:
        """
        Recherche avec scoring intelligent.
        Retourne (element, score) ou None.
        prefer_type: 'clickable' ou 'input' pour filtrer
        """
        elements = self.scan_page_advanced()
        
        if prefer_type:
            elements = [e for e in elements if e["type"] == prefer_type]
        
        if not elements:
            return None
        
        candidates = []  # (score, element, label)
        target_lower = description.lower().strip()
        
        for el in elements:
            # Collecter tous les attributs textuels
            text = (el.get("text") or "").strip()
            aria = (el.get("aria") or "").strip()
            title = (el.get("title") or "").strip()
            placeholder = (el.get("placeholder") or "").strip()
            eid = (el.get("id") or "").strip()
            name = (el.get("name") or "").strip()
            
            # Label = premier non-vide
            label = text or title or aria or placeholder or eid or name
            
            if not label:
                continue
            
            label_lower = label.lower()
            
            # Calcul du score
            score = 0
            
            # 1. Match EXACT = 100
            if label_lower == target_lower:
                score = 100
            
            # 2. Match exact sur un attribut spécifique = 90
            elif any(attr.lower() == target_lower for attr in [text, title, aria, placeholder] if attr):
                score = 90
            
            # 3. Target entièrement dans label = 75 (début) ou 70
            elif target_lower in label_lower:
                score = 75 if label_lower.startswith(target_lower) else 70
            
            # 4. Label entièrement dans target (avec ratio minimum)
            elif label_lower in target_lower:
                ratio = len(label_lower) / len(target_lower)
                if ratio >= 0.4:
                    score = 60
            
            # 5. Mots communs (tous les mots du target dans label)
            target_words = set(target_lower.split())
            label_words = set(label_lower.split())
            
            if target_words and target_words.issubset(label_words):
                score = max(score, 50)
            
            # 6. Au moins 50% des mots en commun
            if target_words and label_words:
                common = target_words & label_words
                if len(common) >= len(target_words) * 0.5:
                    score = max(score, 40)
            
            if score > 0:
                candidates.append((score, el["element"], label))
        
        if not candidates:
            return None
        
        # Trier par score décroissant
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_elem, best_label = candidates[0]
        
        if best_score >= 40:  # Seuil minimum
            logging.info(f"[WebHelper] Match (score {best_score}): '{best_label[:60]}'")
            return (best_elem, best_score)
        
        return None
    
    # ========== ACTIONS ==========
    
    def click_element(self, description: str) -> bool:
        """
        Clique sur un élément via matching intelligent.
        Retourne True si succès, False si échec (→ fallback Vision)
        """
        result = self.find_element_smart(description, prefer_type="clickable")
        
        if not result:
            logging.info(f"[WebHelper] Élément '{description}' non trouvé → Fallback Vision")
            return False
        
        element, score = result
        
        try:
            element.scroll_into_view_if_needed()
            element.click(timeout=3000)
            time.sleep(0.5)
            logging.info(f"[WebHelper] ✓ Cliqué: {description}")
            return True
        except PlaywrightTimeout:
            logging.warning(f"[WebHelper] Timeout clic → Fallback Vision")
            return False
        except Exception as e:
            logging.warning(f"[WebHelper] Erreur clic: {e} → Fallback Vision")
            return False
    
    def type_in_element(self, description: str, text: str) -> bool:
        """Tape du texte dans un input. False = fallback Vision"""
        result = self.find_element_smart(description, prefer_type="input")
        
        if not result:
            logging.info(f"[WebHelper] Input '{description}' non trouvé → Fallback Vision")
            return False
        
        element, score = result
        
        try:
            element.click()
            element.fill('')
            element.fill(text)
            logging.info(f"[WebHelper] ✓ Texte tapé: {description}")
            return True
        except:
            logging.warning(f"[WebHelper] Erreur saisie → Fallback Vision")
            return False
    
    # ========== GESTION POPUPS ROBUSTE ==========
    
    def handle_popups_auto(self) -> bool:
        """
        Ferme popups/cookies automatiquement.
        Retourne True si quelque chose fermé.
        """
        if not self.connected or not self.page:
            return False
        
        closed = False
        
        # Mots-clés dans boutons visibles
        close_keywords = [
            "accepter", "accept", "autoriser", "j'accepte", 
            "tout accepter", "continuer", "fermer", "close", 
            "×", "ok", "compris", "d'accord"
        ]
        
        try:
            # Tous boutons/links visibles
            buttons = self.page.query_selector_all(
                "button:visible, a:visible, div[role='button']:visible, "
                "span[role='button']:visible"
            )
            
            for btn in buttons:
                try:
                    text = btn.text_content().lower().strip()
                    
                    # Correspondance mot-clé + texte court (pas contenu principal)
                    if any(kw in text for kw in close_keywords) and len(text) < 40:
                        if btn.is_visible() and btn.is_enabled():
                            btn.click(timeout=1000)
                            closed = True
                            logging.info(f"[WebHelper] Popup fermé: '{text[:30]}'")
                            time.sleep(0.3)
                            break  # Un seul popup à la fois
                except:
                    continue
        except:
            pass
        
        # Fallback: ESC si aucun bouton trouvé
        if not closed:
            try:
                self.page.keyboard.press('Escape')
                time.sleep(0.2)
            except:
                pass
        
        return closed
    
    # ========== URL & SCRAPING ==========
    
    def get_current_url(self) -> Optional[str]:
        """Retourne URL actuelle ou None"""
        if not self.connected or not self.page:
            return None
        try:
            return self.page.url
        except:
            return None
    
    def get_page_text(self) -> str:
        """Extrait texte visible de la page (pour analyse LLM)"""
        if not self.connected or not self.page:
            return ""
        try:
            return self.page.inner_text("body")
        except:
            return ""
    
    def get_page_html(self) -> str:
        """HTML complet"""
        if not self.connected or not self.page:
            return ""
        try:
            return self.page.content()
        except:
            return ""
    
    # ========== CLEANUP ==========
    
    def close(self):
        """Fermeture propre"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass
