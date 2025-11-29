"""
PlaywrightRouter - Routeur intelligent pour exécution rapide via Playwright
Parse les suggestions VLM #1 et tente exécution DOM avant de passer à Vision
"""
import json
import re
import time
from typing import Optional, Dict
from utils.ollama_client import OllamaClient

class PlaywrightRouter:
    """
    Routeur Playwright : Fast-path pour éviter Vision si possible
    
    Workflow:
    1. Reçoit suggestion VLM #1 (ex: "Clique sur le bouton Login")
    2. Parse avec LLM → {"action": "click", "target": "Login"}
    3. Tente exécution avec WebHelper
    4. Retourne True (succès) ou False (échec → lancer Vision)
    """
    
    def __init__(self, web_helper):
        """
        Args:
            web_helper: Instance de WebHelper (doit être connectée)
        """
        self.web = web_helper
        self.llm = OllamaClient()  # LLM local pour parsing rapide
    
    def _format_elements_for_llm(self, elements: list) -> str:
        """
        Formate les éléments scannés pour le prompt LLM.
        Limite à 50 éléments pour éviter de surcharger le prompt.
        """
        if not elements:
            return "Aucun élément trouvé sur la page."
        
        # Limiter à 50 éléments max
        elements_to_show = elements[:50]
        
        formatted = []
        for idx, elem in enumerate(elements_to_show):
            elem_type = elem.get('type', 'unknown')
            
            # Construire la description de l'élément
            parts = [f"[{elem_type}]"]
            
            # Ajouter les attributs pertinents
            if elem.get('text'):
                parts.append(f"text='{elem['text'][:50]}'")
            if elem.get('aria'):
                parts.append(f"aria='{elem['aria'][:50]}'")
            if elem.get('placeholder'):
                parts.append(f"placeholder='{elem['placeholder'][:50]}'")
            if elem.get('title'):
                parts.append(f"title='{elem['title'][:50]}'")
            if elem.get('id'):
                parts.append(f"id='{elem['id'][:30]}'")
            if elem.get('name'):
                parts.append(f"name='{elem['name'][:30]}'")
            
            formatted.append(f"{idx}. {' '.join(parts)}")
        
        if len(elements) > 50:
            formatted.append(f"\n... et {len(elements) - 50} autres éléments")
        
        return "\n".join(formatted)
    
    def try_fast_path(self, vlm_suggestion: str, task_description: str = "") -> bool:
        """
        Tente d'exécuter la suggestion via Playwright (fast-path).
        
        Args:
            vlm_suggestion: Suggestion du VLM #1 (texte brut)
            task_description: Tâche globale pour contexte
            
        Returns:
            True si action réussie via Playwright
            False si échec → le pipeline Vision doit prendre le relais
        """
        if not self.web or not self.web.connected:
            print("[PlaywrightRouter] WebHelper non disponible → Vision")
            return False
        
        # 1. SCANNER la page AVANT de parser (NOUVEAU)
        print("[PlaywrightRouter] Scanning de la page...")
        available_elements = self.web.scan_page_advanced()
        
        if not available_elements:
            print("[PlaywrightRouter] Aucun élément trouvé → Vision")
            return False
        
        print(f"[PlaywrightRouter] {len(available_elements)} éléments détectés")
        
        # 2. Parser suggestion avec LLM + éléments disponibles
        action_dict = self._parse_suggestion(vlm_suggestion, task_description, available_elements)
        
        if not action_dict:
            print("[PlaywrightRouter] Parsing échec → Vision")
            return False
        
        # 3. Exécuter avec WebHelper
        success = self._execute_playwright_action(action_dict, available_elements)
        
        if success:
            print(f"[PlaywrightRouter] ✅ Succès: {action_dict.get('action')} sur '{action_dict.get('target', '')}'")
        else:
            print(f"[PlaywrightRouter] ❌ Échec → Vision prend le relais")
        
        return success
    
    def _parse_suggestion(self, suggestion: str, task_context: str = "", available_elements: list = None) -> Optional[Dict]:
        """
        Parse suggestion VLM #1 en action Playwright structurée.
        
        Args:
            available_elements: Liste des éléments scannés sur la page (NOUVEAU)
        
        Returns:
            {"action": "click"|"type"|"enter", "target": "texte", "element_index": int, "text": "..."}
            ou None si impossible à parser
        """
        # Formatter les éléments pour le prompt
        elements_text = ""
        if available_elements:
            elements_text = f"\n\nÉLÉMENTS DISPONIBLES SUR LA PAGE:\n{self._format_elements_for_llm(available_elements)}\n"
        
        prompt = f"""Tu es un parser d'actions web. Tu reçois une suggestion et tu dois la convertir en action Playwright.

TÂCHE GLOBALE: {task_context}
SUGGESTION: {suggestion}
{elements_text}
ACTIONS POSSIBLES:
- click: cliquer sur un élément (bouton, lien, etc.)
- type: taper du texte dans un champ
- enter: appuyer sur Entrée
- wait: attendre
- read: extraire/lire le contenu de la page

RÈGLES:
1. Réponds UNIQUEMENT en JSON (pas de texte autour)
2. Si des éléments sont listés, choisis le MEILLEUR élément qui correspond à la suggestion
3. Format pour click: {{"action": "click", "element_index": INDEX, "target": "texte de l'élément"}}
4. Format pour type: {{"action": "type", "element_index": INDEX, "target": "Email", "text": "user@example.com"}}
5. Pour "enter": {{"action": "enter"}}
6. Si pas sûr ou aucun élément ne correspond → renvoie null

EXEMPLES:
Éléments: 0. [button] text='Sign In' | 1. [button] text='Login' | 2. [link] text='Register'
Suggestion: "Clique sur le bouton Login"
Réponse: {{"action": "click", "element_index": 1, "target": "Login"}}

Suggestion: "Tape 'test@mail.com' dans le champ email"
Éléments: 0. [input] placeholder='Email address' | 1. [input] type='password'
Réponse: {{"action": "type", "element_index": 0, "target": "Email address", "text": "test@mail.com"}}

Suggestion: "Cherche météo" ou "Recherche Python"
Éléments: 0. [input] name='q' placeholder='Rechercher'
Réponse: {{"action": "type", "element_index": 0, "target": "Rechercher", "text": "météo", "press_enter": true}}

Analyse et réponds en JSON:"""

        try:
            response = self.llm.generate(prompt, max_tokens=150, temperature=0.0)
            
            # Nettoyer réponse
            response = response.strip()
            
            # Extraire JSON (parfois le LLM ajoute du texte autour)
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                response = json_match.group(0)
            
            # Parser JSON
            action_dict = json.loads(response)
            
            # Valider structure
            if not isinstance(action_dict, dict) or "action" not in action_dict:
                return None
            
            # Normaliser action
            action = action_dict.get("action", "").lower()
            if action not in ["click", "type", "enter", "wait", "read"]:
                return None
            
            print(f"[PlaywrightRouter] LLM a choisi: {action_dict}")
            return action_dict
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"[PlaywrightRouter] Erreur parsing LLM: {e}")
            return None
    
    def _execute_playwright_action(self, action_dict: Dict, available_elements: list = None) -> bool:
        """
        Exécute l'action parsée avec WebHelper.
        
        Args:
            action_dict: Action à exécuter (de _parse_suggestion)
            available_elements: Liste des éléments scannés (NOUVEAU)
        
        Returns:
            True si succès, False si échec
        """
        action = action_dict.get("action", "").lower()
        target = action_dict.get("target", "").strip()
        text = action_dict.get("text", "").strip()
        element_index = action_dict.get("element_index")
        
        try:
            if action == "click":
                if not target:
                    return False
                
                # Si le LLM a fourni un element_index, utiliser l'élément directement
                if element_index is not None and available_elements:
                    if 0 <= element_index < len(available_elements):
                        elem = available_elements[element_index]
                        element_handle = elem.get("element")
                        
                        if element_handle:
                            try:
                                element_handle.scroll_into_view_if_needed()
                                element_handle.click(timeout=3000)
                                print(f"[PlaywrightRouter] ✓ Clic direct sur élément #{element_index}")
                                return True
                            except Exception as e:
                                print(f"[PlaywrightRouter] Erreur clic direct: {e}, fallback sur matching texte")
                
                # Fallback: utiliser matching intelligent de WebHelper
                return self.web.click_element(target)
            
            elif action == "type":
                if not target:
                    return False
                
                press_enter = action_dict.get("press_enter", False)  # ← AJOUTER
                
                # Si le LLM a fourni un element_index, utiliser l'élément directement
                if element_index is not None and available_elements:
                    if 0 <= element_index < len(available_elements):
                        elem = available_elements[element_index]
                        element_handle = elem.get("element")
                        
                        if element_handle:
                            try:
                                element_handle.click()
                                element_handle.fill('')
                                element_handle.fill(text or "")
                                print(f"[PlaywrightRouter] ✓ Saisie directe sur élément #{element_index}")
                                
                                # ✅ NOUVEAU : Appuyer sur Enter si demandé
                                if press_enter:
                                    time.sleep(0.3)  # Petit délai
                                    element_handle.press("Enter")
                                    print(f"[PlaywrightRouter] ✓ Enter pressé")
                                    time.sleep(1)  # Attendre chargement
                                
                                return True
                            except Exception as e:
                                print(f"[PlaywrightRouter] Erreur saisie directe: {e}, fallback sur matching texte")
                
                # Fallback: taper dans input via matching intelligent
                success = self.web.type_in_element(target, text or "")
                
                # ✅ NOUVEAU : Enter aussi en fallback
                if success and press_enter:
                    time.sleep(0.3)
                    if self.web.page:
                        self.web.page.keyboard.press("Enter")
                        print(f"[PlaywrightRouter] ✓ Enter pressé")
                        time.sleep(1)
                
                return success
            
            elif action == "enter":
                # Appuyer sur Entrée
                if self.web.page:
                    self.web.page.keyboard.press("Enter")
                    time.sleep(0.5)
                    return True
                return False
            
            elif action == "wait":
                duration = action_dict.get("duration", 1)
                time.sleep(duration)
                return True
            elif action == "read":
    # Extraire le contenu de la page
                if self.web.page:
                    content = self.web.get_page_text()
                    print(f"[PlaywrightRouter] ✓ Contenu extrait ({len(content)} caractères)")
                    # TODO: Stocker dans contexte pour file_manager
                    return True
                return False
            else:
                print(f"[PlaywrightRouter] Action inconnue: {action}")
                return False
                
        except Exception as e:
            print(f"[PlaywrightRouter] Erreur exécution: {e}")
            return False
    
    def close(self):
        """Cleanup (si nécessaire)"""
        pass
