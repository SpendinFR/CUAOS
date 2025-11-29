"""
Task Orchestrator - Orchestrateur Intelligent Multi-Tâches
Gère l'exécution de tâches complexes en choisissant dynamiquement les bons skills
"""
import json
import time
import webbrowser
from typing import Dict, List, Any, Optional
from pathlib import Path


class TaskOrchestrator:
    """
    Orchestrateur intelligent qui:
    1. Analyse la tâche globale
    2. Crée un plan multi-étapes
    3. Choisit le bon skill à chaque étape
    4. Décide à chaque fin de boucle: continuer/changer/terminer
    5. Maintient l'état de progression
    """
    
    def __init__(self, llm_client):
        """
        Args:
            llm_client: Instance OllamaClient pour décisions LLM
        """
        self.llm = llm_client
        
        # État global
        self.global_task = ""
        self.task_plan = []
        self.completed_steps = []
        self.current_context = {}
        self.current_skill = None
        
        # Skills disponibles (lazy load)
        self.skills = {
            "open_url": None,  # Fonction simple
            "web_helper": None,  # WebHelper instance
            "cua_vision": None,  # CUAAgent instance
            "file_manager": None,  # FileManager instance
            "app_launcher": None,  # AppLauncher instance
            "run_command": None  # Fonction
        }
    
    def execute_task(self, task_description: str) -> Dict:
        """
        Point d'entrée principal de l'orchestrateur
        
        Args:
            task_description: Description de la tâche à accomplir
        
        Returns:
            {
                "success": bool,
                "summary": str,  # Pour que Executeur décide quoi dire
                "result": any,
                "error": str (si échec)
            }
        """
        print(f"\n{'='*60}")
        print(f"[Orchestrator] Tâche: {task_description}")
        print(f"{'='*60}\n")
        
        self.global_task = task_description
        # ✅ RESET STATE pour nouvelle tâche
        self.task_plan = []
        self.completed_steps = []
        self.current_context = {}
        self.current_skill = None
        
        try:
            # 1. Analyser et créer le plan initial
            print("[Orchestrator] Création du plan initial...")
            self.task_plan = self._create_initial_plan()
            print(f"[Orchestrator] Plan: {len(self.task_plan)} étapes")
            
            # 2. Boucle d'exécution
            max_iterations = 20  # Sécurité anti-boucle infinie
            iteration = 0
            
            # ✅ NOUVEAU : Tracking des actions pour détecter boucles
            action_history_tracker = []
            while iteration < max_iterations:
                iteration += 1
                print(f"\n[Orchestrator] --- Itération {iteration} ---")
                
                # Décider de la prochaine action
                decision = self._decide_next_action()
                print("DEBUG décision brute:", decision, flush=True)
                import sys
                sys.stdout.flush()
                
                # Vérifier si tâche terminée
                if decision.get("task_complete", False):
                    print("[Orchestrator] ✅ Tâche complète !")
                    break
                
                # ✅ NOUVEAU : Détecter boucle infinie (même skill répété 3 fois)
                current_skill = decision.get("next_skill") or self.current_skill
                action_history_tracker.append(current_skill)
                
                if len(action_history_tracker) >= 6:
                    last_6 = action_history_tracker[-6:]
                    # Vérifier pattern répétitif (ex: ABABAB)
                    if last_6[0] == last_6[2] == last_6[4] and last_6[1] == last_6[3] == last_6[5]:
                        print(f"[Orchestrator] ❌ BOUCLE INFINIE DÉTECTÉE: {last_6}")
                        print(f"[Orchestrator] Pattern: {last_6[0]} ↔ {last_6[1]} répété 3 fois")
                        break
                
                # Exécuter l'action avec le skill choisi
                result = self._execute_action(decision)
                
                # Mettre à jour l'état
                self._update_state(decision, result)
            
            # 3. Retourner résumé pour Executeur
            summary = self._generate_summary()
            
            return {
                "success": True,
                "summary": summary,
                "result": self.current_context,
                "steps_count": len(self.completed_steps)
            }
        
        except Exception as e:
            print(f"[Orchestrator] ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "summary": f"Erreur lors de l'exécution: {str(e)}",
                "error": str(e)
            }
    
    def _create_initial_plan(self) -> List[Dict]:
        """Crée un plan initial avec le LLM"""
        
        prompt = f"""Tâche: {self.global_task}

Analyse cette tâche et crée un plan d'action concis.

Skills disponibles:
- open_url: Ouvrir une URL : "start https://url.com"
- web_helper: Navigation web assistée (Playwright)
- cua_vision: Navigation web autonome (vision)
- file_manager: Créer/Lire/Gérer fichiers et dossiers
- app_launcher: Lancer applications de bureau uniquement 
- run_command: Commande système Windows

Exemples:
- "va sur youtube cherche messi":
  Step 1: open_url → https://youtube.com/results?search_query=messi
  Step 2: cua_vision → cliquer première vidéo


Retourne UNIQUEMENT un JSON valide (pas de texte avant/après):
{{
    "steps": [
        {{"step": 1, "description": "...", "estimated_skill": "..."}},
        {{"step": 2, "description": "...", "estimated_skill": "..."}}
    ],
    "complexity": "simple|medium|complex"
}}"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=500, temperature=0.3)
            # Nettoyer la réponse pour extraire le JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            plan = json.loads(response)
            return plan.get("steps", [])
        except Exception as e:
            print(f"[Orchestrator] Erreur création plan: {e}")
            # Plan par défaut
            return [
                {"step": 1, "description": self.global_task, "estimated_skill": "cua_vision"}
            ]
    
    def _decide_next_action(self) -> Dict:
        """
        DÉCISION CRITIQUE à chaque fin de boucle
        
        Le LLM décide:
        - Continuer avec le skill actuel?
        - Changer de skill?
        - Tâche terminée?
        """
        # ✅ À l'itération 1, exécuter directement le premier step du plan
        if len(self.completed_steps) == 0 and len(self.task_plan) > 0:
            step = self.task_plan[0]
            return {
                "continue_current_skill": False,
                "next_skill": step["estimated_skill"],
                "skill_instruction": step["description"],
                "task_complete": False,
                "reason": "Démarrage du plan"
            }
        # ✅ Si CUA a terminé ET que c'était le dernier step du plan → terminer
        if self.current_context.get("cua_complete") and len(self.completed_steps) >= len(self.task_plan):
            print("[Orchestrator] ✅ CUA terminé + plan complet → Tâche finie")
            return {
                "continue_current_skill": False,
                "task_complete": True,
                "summary": f"Tâche terminée avec succès en {len(self.completed_steps)} étapes"
            }
        # Ensuite, demander au LLM
        prompt = f"""# CONTEXTE
Tâche globale: {self.global_task}
Plan initial: {json.dumps(self.task_plan, ensure_ascii=False)}

# ÉTAT ACTUEL
Étapes complétées: {len(self.completed_steps)}
Skill actuellement actif: {self.current_skill or "Aucun"}
Application desktop lancée: {self.current_context.get('app', 'Aucune')}  ← AJOUTER
Contexte: {self._sanitize_context_for_prompt()}

RÈGLE ABSOLUE: Si une application DESKTOP a été lancée (Spotify, Discord, etc.), 
utilise OBLIGATOIREMENT le skill cua_vision pour interagir avec elle et marque current_skill : false
Ne jamais utiliser applancher pour intéragir avec une application desktop !
NE JAMAIS utiliser web_helper pour une application desktop !
# DÉCISION REQUISE
Analyse l'état actuel et décide de la prochaine action.

Questions:
1. Le skill actuel a-t-il terminé sa sous-tâche?
2. Faut-il continuer avec ce skill ou en changer?
3. La tâche globale est-elle terminée?

Retourne UNIQUEMENT un JSON valide:
{{
    "continue_current_skill": true|false,
    "reason": "explication courte",
    
    "next_instruction": "instruction si continue_current_skill=true",
    
    "next_skill": "nom du skill si continue_current_skill=false",
    "skill_instruction": "instruction pour le nouveau skill",
    
    "task_complete": true|false,
    "summary": "résumé si task_complete=true"
}}

IMPORTANT:
- Si CUA Vision actif et navigation pas terminée → continue_current_skill = true
- Si objectif atteint → change de skill si besoin ou task_complete

*** RÈGLES CRITIQUES SKILLS ***
- open_url = UNIQUEMENT itération 1 pour ouvrir l'URL initiale
- web_helper = Pour actions web  SIMPLES (cliquer bouton connu, taper texte, lire page)
*Lire la page se termine en 1 seul appel
*NE PAS utiliser web_helper pour applications desktop
  Exemples web_helper: "Cliquer sur Login", "Chercher météo", "Lire contenu page"
- cua_vision = Pour actions web COMPLEXES nécessitant vision ou pour naviguer dans pour naviguer dans les applications desktop (localiser élément visuellement)
  Exemples cua_vision: "Cliquer sur la 3e vidéo", "Sélectionner article avec image de chat, faire une action dans une application"
- SI web_helper échoue ou renvoie none → IMMÉDIATEMENT passer à cua_vision
- app_launcher = UNIQUEMENT itération 1 pour ouvrir une application desktop (lancer applications de bureau uniquement)
*** NE JAMAIS utiliser open_url pour naviguer ou chercher ***"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=400, temperature=0.2)
            
            # ✅ Parse robuste avec nouvelle méthode
            decision = self._extract_and_parse_json(response)
            
            # ✅ Forcer cua_vision si on a déjà fait open_url
            if len(self.completed_steps) >= 1 and decision and decision.get("next_skill") == "open_url":
                print("[Orchestrator] ⚠️ Forcing cua_vision (open_url déjà  utilisé)")
                decision["next_skill"] = "cua_vision"
            
            if not decision:
                # Fallback: utiliser cua_vision par défaut
                print("[Orchestrator] ⚠️ Erreur parsing JSON, fallback CUA Vision")
                return {
                    "continue_current_skill": False,
                    "next_skill": "cua_vision",
                    "skill_instruction": self.global_task,
                    "task_complete": False,
                    "reason": "Erreur parsing, fallback CUA"
                }
            
            print(f"[Orchestrator] Décision: {decision.get('reason', 'N/A')}")
            return decision
            
        except Exception as e:
            print(f"[Orchestrator] Erreur décision: {e}")
            # ✅ NE PAS marquer task_complete !
            return {
                "continue_current_skill": False,
                "next_skill": "cua_vision",
                "skill_instruction": self.global_task,
                "task_complete": False
            }
    
    def _execute_action(self, decision: Dict) -> Any:
        """Exécute l'action avec le skill approprié"""
        print(f"[DEBUG _execute_action] ENTRÉE, decision={decision}")  # ← AJOUTER
        if decision.get("continue_current_skill", False):
            # Continuer avec le skill actuel
            skill_name = self.current_skill
            instruction = decision.get("next_instruction", "")
        else:
            # Changer de skill
            skill_name = decision.get("next_skill", "")
            instruction = decision.get("skill_instruction", "")
            self.current_skill = skill_name
        
        if not skill_name or not instruction:
            print("[Orchestrator] Pas d'action à exécuter")
            return {"success": False, "error": "No action"}
        
        # Exécuter avec le skill
        print(f"[Orchestrator] Skill: {skill_name}")
        print(f"[Orchestrator] Instruction: {instruction}")
        
        print(f"[DEBUG] AVANT appel _call_skill")
        try:
            result = self._call_skill(skill_name, instruction)
            print(f"[DEBUG] APRÈS appel _call_skill, result={result}")
        except Exception as e:
            print(f"[DEBUG] EXCEPTION dans _call_skill: {e}")
            import traceback
            traceback.print_exc()
            result = {"success": False, "error": str(e)}        
        # ✅ Si CUA Vision termine, marquer tâche complète
        if skill_name == "cua_vision" and isinstance(result, dict):
            if result.get("task_complete") == True:
                print("[Orchestrator] ✅ CUA Vision a terminé la tâche")
                self.current_context["cua_complete"] = True
        
        return result
    
    def _call_skill(self, skill_name: str, instruction: str) -> Any:
        """Appelle le skill approprié"""
        try:
            if skill_name == "open_url":
                # ✅ L'instruction peut être une URL OU du texte → nettoyer
                instruction = instruction.strip()
                
                # Si c'est déjà une URL valide, utiliser direct
                if instruction.startswith("http"):
                    url = instruction
                else:
                    # Sinon, demander au LLM de générer l'URL
                    url_prompt = f"""Instruction: {instruction}
                    
Tâche globale: {self.global_task}

Retourne UNIQUEMENT l'URL complète (format: https://...).

Règles:
- YouTube recherche: https://youtube.com/results?search_query=X
- Google: https://google.com
- Site direct: https://site.com

Retourne UNIQUEMENT l'URL, rien d'autre."""

                    url = self.llm.generate(url_prompt, max_tokens=100, temperature=0.0).strip()
                    # Nettoyer
                    url = url.replace('"', '').replace("'", '').strip()
                    if not url.startswith("http"):
                        url = "https://" + url
                
                print(f"[Orchestrator] URL finale: {url}")
                
                # Déléguer à app_launcher
                if self.skills["app_launcher"] is None:
                    try:
                        from actions.app_launcher import AppLauncher
                        self.skills["app_launcher"] = AppLauncher()
                    except Exception as e:
                        return {"success": False, "error": str(e)}
                
                result = self.skills["app_launcher"].launch_url(url)
                
                # ✅ Vérifier si cette URL termine la tâche globale
                time.sleep(2)
                check_prompt = f"""Tâche globale: {self.global_task}
J'ai ouvert l'URL: {url}

Est-ce que la tâche est COMPLÈTE maintenant (objectif atteint) ?
Réponds JSON: {{"complete": true/false}}"""

                try:
                    response = self.llm.generate(check_prompt, max_tokens=50, temperature=0.0)
                    check = self._extract_and_parse_json(response)
                    if check and check.get("complete"):
                        print(f"[Orchestrator] ✅ open_url a complété la tâche globale")
                        self.current_context["url_task_complete"] = True
                except Exception as e:
                    print(f"[Orchestrator] Check completion failed: {e}")
                
                return {"success": result, "url": url, "method": "app_launcher"}
            
            elif skill_name == "web_helper":
                # ✅ Check Chrome AVANT (s'exécute TOUJOURS)
                from config import CHROME_DEBUG_PORT
                import socket
                
                sock = socket.socket()
                chrome_running = sock.connect_ex(('localhost', CHROME_DEBUG_PORT)) == 0
                sock.close()
                
                if not chrome_running:
                    print(f"[Orchestrator] Chrome debug pas lancé → auto-launch")
                    self._call_skill("open_url", "https://google.com")
                
                # Init WebHelper (si pas déjà fait)
                if self.skills["web_helper"] is None:
                    try:
                        from actions.web_helper import WebHelper
                        web_instance = WebHelper(debug_port=CHROME_DEBUG_PORT)
                        
                        # ✅ AJOUTER CE DEBUG :
                        print(f"[Orchestrator] DEBUG web_instance.connected = {web_instance.connected}")
                        print(f"[Orchestrator] DEBUG web_instance.page = {web_instance.page}")
                        
                        if not web_instance.page:
                            success = web_instance.refresh_connection()
                            
                            # ✅ AJOUTER CE DEBUG :
                            print(f"[Orchestrator] DEBUG refresh_connection() = {success}")
                            print(f"[Orchestrator] DEBUG web_instance.page après refresh = {web_instance.page}")
                            
                            if not success or not web_instance.page:
                                print(f"[Orchestrator] ❌ WebHelper: Aucune page Chrome active")
                                print(f"[Orchestrator] → Fallback CUA Vision")
                                return self._call_skill("cua_vision", instruction)
                        self.skills["web_helper"] = web_instance
                    except Exception as e:
                        print(f"[Orchestrator] WebHelper indisponible: {e}")
                        return {"success": False, "error": f"WebHelper unavailable: {e}"}
                
                print(f"[Orchestrator] 📞 Appel de _execute_web_helper()...")
                result = self._execute_web_helper(instruction)
                print(f"[Orchestrator] 📥 Résultat: {result}")
                
                # ✅ Si user intervention nécessaire → Passer à CUA
                if result.get("user_intervention_needed"):
                    print(f"[Orchestrator] 👤 WebHelper demande intervention → Passage CUA")
                    print(f"[Orchestrator] Raison: {result.get('reason', 'N/A')}")
                    return self._call_skill("cua_vision", instruction)
                
                return result
            elif skill_name == "cua_vision":
                # CUA Vision pour navigation autonome
                if self.skills["cua_vision"] is None:
                    try:
                        from actions.cua_agent import CUAAgent
                        self.skills["cua_vision"] = CUAAgent()
                        print("[Orchestrator] CUA Vision chargé")
                    except Exception as e:
                        print(f"[Orchestrator] CUA Vision indisponible: {e}")
                        return {"success": False, "error": f"CUA unavailable: {e}"}
                
                # Exécuter avec max_steps limité pour permettre retour fréquent
                result = self.skills["cua_vision"].execute_task(instruction, max_steps=10)
                return result
            
            elif skill_name == "file_manager":
                # FileManager pour gestion fichiers
                if self.skills["file_manager"] is None:
                    try:
                        from actions.file_manager import FileManager
                        self.skills["file_manager"] = FileManager()
                        print("[Orchestrator] FileManager chargé")
                    except Exception as e:
                        print(f"[Orchestrator] FileManager indisponible: {e}")
                        return {"success": False, "error": f"FileManager unavailable: {e}"}
                
                print(f"[Orchestrator] 📞 Appel de _execute_file_manager()...")
                result = self._execute_file_manager(instruction)
                print(f"[Orchestrator] 📥 Résultat: {result}")
                return result

            elif skill_name == "app_launcher":
                # AppLauncher pour lancer apps
                if self.skills["app_launcher"] is None:
                    try:
                        from actions.app_launcher import AppLauncher
                        self.skills["app_launcher"] = AppLauncher()
                        print("[Orchestrator] AppLauncher chargé")
                    except Exception as e:
                        print(f"[Orchestrator] AppLauncher indisponible: {e}")
                        return {"success": False, "error": f"AppLauncher unavailable: {e}"}
                
                # ✅ Extraire le nom de l'app depuis l'instruction
                app_name = self._extract_app_name(instruction)
                print(f"[Orchestrator] App extraite: '{app_name}'")
                return self.skills["app_launcher"].launch_app(app_name)
            
            elif skill_name == "gui_controller":
                # GUIController pour contrôle OS
                if self.skills["gui_controller"] is None:
                    try:
                        from actions.gui_controller import GUIController
                        self.skills["gui_controller"] = GUIController()
                    except Exception as e:
                        print(f"[Orchestrator] GUIController indisponible: {e}")
                        return {"success": False, "error": f"GUIController unavailable: {e}"}
                
                # Parse instruction pour déterminer action (à implémenter selon besoin)
                return {"success": True, "action": instruction}
            
            elif skill_name == "run_command":
                # Commande système
                import subprocess
                result = subprocess.run(
                    instruction,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None
                }
            
            else:
                print(f"[Orchestrator] Skill inconnu: {skill_name}")
                return {"success": False, "error": f"Unknown skill: {skill_name}"}
        
        except Exception as e:
            print(f"[Orchestrator] Erreur exécution {skill_name}: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _execute_web_helper(self, instruction: str) -> Dict:
        """Exécute une instruction WebHelper avec intelligence LLM"""
        web = self.skills["web_helper"]
        
        # ✅ Vérifier connexion
        if not web.connected:
            print(f"[WebHelper] ❌ Non connecté")
            return {"success": False, "error": "WebHelper not connected"}
        # ✅ NOUVEAU : Vérifier que page existe
        if not web.page:
            print(f"[WebHelper] ❌ Aucune page active")
            return {"success": False, "error": "No active page"}
        
        try:
            print(f"[WebHelper] Analyse page pour: {instruction}")
                
            # Scanner éléments avec Playwright
            elements = web.scan_page_advanced()
                
            # Extraire texte visible
            page_text = web.get_page_text()
                
            # Obtenir URL actuelle
            current_url = web.get_current_url()
            
            # ✅ ÉTAPE 2 : LLM décide quelle action Playwright faire
            prompt = f"""Tu es un assistant web automation avec Playwright.

PAGE ACTUELLE:
URL: {current_url}
Texte visible (500 premiers caractères): {page_text[:500] if page_text else "Vide"}
Nombre d'éléments clickables trouvés: {len([e for e in elements if e.get('type') == 'clickable'])}
Nombre d'inputs trouvés: {len([e for e in elements if e.get('type') == 'input'])}
ÉLÉMENTS DISPONIBLES SUR LA PAGE:
{self._format_elements_for_llm(elements)}
TÂCHE À ACCOMPLIR: {instruction}

ACTIONS DISPONIBLES:
1. "click" - Cliquer sur un élément (bouton, lien, etc.)
2. "type" - Taper du texte dans un input
3. "read" - Lire et extraire le contenu de la page
4. "wait" - Attendre que la page charge
5. "navigate" - Aller vers une URL différente connu (exemple: de google.com vers gmail.com)
6. "user_input_required" - Demander à l'utilisateur (email, password, CAPTCHA, etc.)
7. "none" - Aucune action nécessaire (déjà fait)

RÈGLES NAVIGATION INTELLIGENTE:
1. Si la tâche contient "chercher", "rechercher", "trouver" → utilise "type" dans la barre de recherche
2. Pour navigate : vérifier URL et aller vers URL différente connue
3. Utilise "none" SEULEMENT si la tâche est déjà complètement accomplie
4. Si la tâche contient "lire", "copier", "extraire", "récupérer le contenu" → utilise "read" 

Analyse la situation et décide quelle action faire.

Retourne UNIQUEMENT un JSON valide:
{{
  "action": "click" | "type" | "read" | "wait" | "navigate" | "user_input_required" | "none",
  "element_index": INDEX (numéro de l'élément dans la liste ci-dessus),
  "target": "description de l'élément cible (si click ou type)",
  "text": "texte à taper (si type)",
  "press_enter": true/false (si type, pour valider la recherche),
  "url": "URL complète (si navigate, exemple: https://gmail.com)",
  "reason": "explication courte",
  "success_indicator": "texte qui apparaîtra si succès"
}}

Exemples:
- Pour "Lire le dernier email" → {{"action": "click", "element_index": 5, "target": "premier email liste", "reason": "Cliquer pour ouvrir"}}
- Pour "Chercher météo" → {{"action": "type", "element_index": 19, "target": "Rechercher", "text": "météo", "press_enter": true, "reason": "Rechercher météo"}}
- Pour "Lire contenu page" ou "Copier le résultat"→ {{"action": "read", "reason": "Extraire texte visible"}}
"""
            
            # Générer décision
            response = self.llm.generate(prompt, max_tokens=300, temperature=0.1)
            
            # Parser JSON
            import json
            import re
            
            # Nettoyer réponse
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Extraire JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                return {"success": False, "error": "LLM response invalid"}
            
            print(f"[WebHelper] LLM décision: {decision.get('action')} - {decision.get('reason')}")
            
            # ✅ ÉTAPE 3 : Exécuter l'action décidée
            action_success = False
            result_data = {}
            
            if decision["action"] == "click":
                target = decision.get("target", "")
                element_index = decision.get("element_index")  # ← NOUVEAU
                
                result_data["action"] = "click"
                result_data["target"] = target
                
                # ✅ NOUVEAU : Si element_index fourni, utiliser l'élément directement
                if element_index is not None and 0 <= element_index < len(elements):
                    elem = elements[element_index]
                    element_handle = elem.get("element")
                    
                    if element_handle:
                        try:
                            element_handle.scroll_into_view_if_needed()
                            element_handle.click(timeout=3000)
                            print(f"[WebHelper] ✓ Clic direct sur élément #{element_index}")
                            time.sleep(2)
                            action_success = True
                        except Exception as e:
                            print(f"[WebHelper] Erreur clic direct: {e}, fallback matching texte")
                            action_success = web.click_element(target)
                    else:
                        action_success = web.click_element(target)
                else:
                    # Fallback: matching intelligent
                    action_success = web.click_element(target)
                
                if action_success:
                    print(f"[WebHelper] ✅ Cliqué sur: {target}")
                else:
                    print(f"[WebHelper] ❌ Échec clic sur: {target}")
            
            elif decision["action"] == "type":
                target = decision.get("target", "")
                text = decision.get("text", "")
                press_enter = decision.get("press_enter", False)  # ← NOUVEAU
                element_index = decision.get("element_index")  # ← NOUVEAU
                
                result_data["action"] = "type"
                result_data["target"] = target
                
                # ✅ NOUVEAU : Si element_index fourni, utiliser l'élément directement
                if element_index is not None and 0 <= element_index < len(elements):
                    elem = elements[element_index]
                    element_handle = elem.get("element")
                    
                    if element_handle:
                        try:
                            element_handle.click()
                            element_handle.fill('')
                            element_handle.fill(text or "")
                            print(f"[WebHelper] ✓ Saisie directe sur élément #{element_index}")
                            
                            # Appuyer sur Enter si demandé
                            if press_enter:
                                time.sleep(0.3)
                                element_handle.press("Enter")
                                print(f"[WebHelper] ✓ Enter pressé")
                                time.sleep(1.5)  # Attendre chargement résultats
                            
                            action_success = True
                        except Exception as e:
                            print(f"[WebHelper] Erreur saisie directe: {e}, fallback matching texte")
                            # Fallback ci-dessous
                            action_success = False
                    else:
                        action_success = False
                else:
                    action_success = False
                
                # Fallback: matching intelligent si element_index échoue
                if not action_success:
                    action_success = web.type_in_element(target, text)
                    
                    if action_success:
                        print(f"[WebHelper] ✅ Tapé '{text}' dans: {target}")
                        
                        # Enter en fallback aussi
                        if press_enter and web.page:
                            time.sleep(0.3)
                            web.page.keyboard.press("Enter")
                            print(f"[WebHelper] ✓ Enter pressé")
                            time.sleep(1.5)
                    else:
                        print(f"[WebHelper] ❌ Échec saisie dans: {target}")
            
            elif decision["action"] == "read":
                content = web.get_page_text()
                action_success = True
                result_data["action"] = "read"
                result_data["content"] = content  # ← Enlever limite 1000 caractères
                
                # ✅ NOUVEAU : Stocker dans contexte avec clé explicite
                result_data["extracted_web_content"] = content
                result_data["content_length"] = len(content)
                
                print(f"[WebHelper] ✅ Contenu extrait ({len(content)} caractères)")
                print(f"[WebHelper] 📝 Stocké dans contexte: 'extracted_web_content'")
            
            elif decision["action"] == "wait":
                time.sleep(2)
                action_success = True
                result_data["action"] = "wait"
                print(f"[WebHelper] ⏳ Attente chargement...")
            
            elif decision["action"] == "navigate":
                url = decision.get("url", "")
                if url:
                    try:
                        web.page.goto(url, timeout=10000)  # 10s timeout
                        action_success = True
                        result_data["action"] = "navigate"
                        result_data["url"] = url
                        print(f"[WebHelper] 🌐 Navigation vers: {url}")
                        time.sleep(2)  # Laisser page charger
                    except Exception as e:
                        print(f"[WebHelper] ❌ Navigation failed: {e}")
                        action_success = False
                else:
                    print(f"[WebHelper] ❌ URL manquante pour navigate")
                    action_success = False
            
            elif decision["action"] == "user_input_required":
                reason = decision.get("reason", "Input utilisateur requis")
                print(f"[WebHelper] 👤 Intervention utilisateur: {reason}")
                action_success = False
                result_data["action"] = "user_input_required"
                result_data["user_intervention_needed"] = True
                result_data["reason"] = reason
            
            elif decision["action"] == "none":
                action_success = True
                result_data["action"] = "none"
                print(f"[WebHelper] ✅ Aucune action nécessaire")
            
            else:
                return {"success": False, "error": f"Action inconnue: {decision['action']}"}
            
            # ✅ ÉTAPE 4 : Vérifier succès (si indicateur fourni)
            if action_success and decision.get("success_indicator"):
                time.sleep(1)
                new_page_text = web.get_page_text()
                
                # Vérifier si indicateur présent
                indicator = decision["success_indicator"].lower()
                if indicator in new_page_text.lower():
                    print(f"[WebHelper] ✅ Succès vérifié: '{indicator}' trouvé")
                    result_data["verified"] = True
                else:
                    print(f"[WebHelper] ⚠️ Indicateur '{indicator}' non trouvé")
                    result_data["verified"] = False
            
            # ✅ RETOUR
            return {
                "success": action_success,
                **result_data
            }
        
        except Exception as e:
            error_msg = str(e).lower()
            
            # ✅ Context destroyed = Page a navigué pendant l'action (normal)
            if "context was destroyed" in error_msg or "execution context" in error_msg:
                print(f"[WebHelper] ⚠️ Page a navigué pendant l'action (normal)")
                # Retourner success=True, l'orchestrator continuera avec la nouvelle page
                return {
                    "success": True, 
                    "action": "page_navigation",
                    "note": "Page changed during action"
                }
            
            # ✅ Timeout = Page lente
            elif "timeout" in error_msg:
                print(f"[WebHelper] ⚠️ Timeout - page trop lente")
                return {
                    "success": False,
                    "error": "Timeout",
                    "retriable": True
                }
            
            # Autres erreurs
            print(f"[WebHelper] ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _execute_file_manager(self, instruction: str) -> Dict:
        """Exécute une instruction FileManager avec intelligence LLM"""
        fm = self.skills["file_manager"]
        
        try:
            # ✅ NOUVEAU : Extraire le contenu web du contexte (s'il existe)
            web_content = self.current_context.get("extracted_web_content", "")
            web_content_preview = web_content[:2000] if web_content else "Aucun contenu web disponible"
            
            # ✅ LLM décide quelle action FileManager faire
            prompt = f"""Tu es un assistant de gestion de fichiers.
    INSTRUCTION: {instruction}
    CONTEXTE:
    - Bureau: {fm.get_desktop_path()}
    - Documents: {fm.get_documents_path()}
    - Home: {fm.get_home_path()}
    CONTENU WEB DISPONIBLE (extrait précédemment):
    {web_content_preview}
    ACTIONS DISPONIBLES:
    1. "create" - Créer un fichier avec contenu
    2. "read" - Lire un fichier existant
    3. "delete" - Supprimer un fichier
    4. "list" - Lister contenu d'un dossier
    Analyse l'instruction et décide quelle action faire.
    IMPORTANT: Si tu dois créer un fichier avec le contenu web, FILTRE et RÉSUME 
    les informations pertinentes (ne copie pas tout).
    Retourne UNIQUEMENT un JSON valide:
    {{
    "action": "create" | "read" | "delete" | "list",
    "filepath": "chemin complet du fichier (utiliser Desktop/nom.txt pour bureau)",
    "content": "contenu du fichier (si create) - FILTRE les infos pertinentes",
    "reason": "explication courte"
    }}
    Exemples:
    - "Créer fichier meteo.txt sur le bureau avec température 15°C" → {{"action": "create", "filepath": "Desktop/meteo.txt", "content": "Température: 15°C\\nHumidité: 60%", "reason": "Créer fichier météo"}}
    - "Lire fichier notes.txt" → {{"action": "read", "filepath": "notes.txt", "reason": "Lire notes"}}
    """
            
            # Générer décision
            response = self.llm.generate(prompt, max_tokens=200, temperature=0.1)
            # just after: response = self.llm.generate(...)
            print(f"[FORCED-TRACE] raw LLM response (len={len(response)}): {response!r}")

            # Parser JSON
            import json
            import re
            
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                return {"success": False, "error": "LLM response invalid"}
            
            print(f"[FileManager] LLM décision: {decision.get('action')} - {decision.get('reason')}")
            
            # ✅ Exécuter l'action
            action = decision.get("action")
            filepath = decision.get("filepath", "")
            
            # Résoudre chemin (Desktop → chemin complet)
            if filepath.startswith("Desktop/"):
                filepath = str(Path(fm.get_desktop_path()) / filepath[8:])
            elif filepath.startswith("Documents/"):
                filepath = str(Path(fm.get_documents_path()) / filepath[10:])
            
            if action == "create":
                content = decision.get("content", "")
                result = fm.create_file(filepath, content)
                return {
                    "success": result,
                    "action": "create",
                    "filepath": filepath
                }
            
            elif action == "read":
                content = fm.read_file(filepath)
                return {
                    "success": content is not None,
                    "action": "read",
                    "filepath": filepath,
                    "content": content[:500] if content else ""  # Limiter taille
                }
            
            elif action == "delete":
                result = fm.delete_file(filepath, confirm=False)
                return {
                    "success": result,
                    "action": "delete",
                    "filepath": filepath
                }
            
            elif action == "list":
                items = fm.list_directory(filepath)
                return {
                    "success": True,
                    "action": "list",
                    "items": items
                }
            
            else:
                return {"success": False, "error": f"Action inconnue: {action}"}
        
        except Exception as e:
            print(f"[FileManager] ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _update_state(self, decision: Dict, result: Any):
        """Met à jour l'état après exécution"""
        
        step_info = {
            "skill": self.current_skill,
            "instruction": decision.get("next_instruction") or decision.get("skill_instruction"),
            "result": result,
            "timestamp": time.time()
        }
        
        self.completed_steps.append(step_info)
        
        # Mettre à jour le contexte avec le résultat
        if isinstance(result, dict):
            self.current_context.update(result)
            # ✅ NOUVEAU : Logger ce qui est ajouté au contexte
            print(f"[Orchestrator] Contexte mis à jour. Clés: {list(result.keys())}")
        else:
            self.current_context["last_result"] = result
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
    
    def _generate_summary(self) -> str:
        """Génère un résumé pour l'Executeur"""
        
        prompt = f"""Tâche demandée: {self.global_task}

{len(self.completed_steps)} actions effectuées

Résultat final: {json.dumps(self.current_context, ensure_ascii=False)[:300]}

Génère un résumé COURT (1-2 phrases) de ce qui a été accompli.
Ce résumé sera utilisé pour répondre à l'utilisateur."""
        
        try:
            summary = self.llm.generate(prompt, max_tokens=100, temperature=0.3)
            return summary.strip()
        except Exception as e:
            return f"Tâche exécutée avec {len(self.completed_steps)} étapes"
    
    def _extract_and_parse_json(self, text: str):
        """Extraction robuste du JSON depuis réponse LLM"""
        import re
        
        # Nettoyer markdown
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Essayer parsing direct
        try:
            return json.loads(text)
        except:
            pass
        
        # Extraire JSON avec regex
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        
        return None
    
    def _sanitize_context_for_prompt(self) -> str:
        """Nettoie context pour inclure dans prompt LLM"""
        safe_context = {}
        for key, value in self.current_context.items():
            if isinstance(value, (str, int, float, bool, list, dict)):
                safe_context[key] = value
            else:
                # Convertir objets non-serializable en string
                safe_context[key] = str(value)[:100]
        
        try:
            return json.dumps(safe_context, ensure_ascii=False)[:500]
        except:
            return str(safe_context)[:500]
    
    def _extract_app_name(self, instruction: str) -> str:
        """Extrait nom d'app depuis instruction LLM"""
        import re
        
        # Keywords à supprimer
        remove_words = ['lancer', 'ouvrir', 'ouvre', 'lance', 'application', "l'application", 'la', 'le']
        
        words = instruction.lower().split()
        filtered = [w for w in words if w not in remove_words]
        
        # Retourner ce qui reste
        return ' '.join(filtered) if filtered else instruction