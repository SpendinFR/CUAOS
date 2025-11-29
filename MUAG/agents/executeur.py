import subprocess
import json
from .diagnostic import AgentDiagnostic
from .verificateur import Verificateur
from utils.ollama_client import OllamaClient
from utils.interaction_utilisateur import InterfaceUtilisateur
from .memory_manager import MemoryManager
from .user_profile import UserProfile

# Import action modules (NO Playwright/WebNavigator!)
try:
    from actions.gui_controller import GUIController
    from actions.file_manager import FileManager
    from actions.app_launcher import AppLauncher
    from actions.cua_agent import CUAAgent
except ImportError as e:
    print(f"Warning: Some action modules not available: {e}")
    GUIController = None
    FileManager = None
    AppLauncher = None
    CUAAgent = None

class Executeur:
    def __init__(self):
        self.client = OllamaClient()
        self.diagnostic = AgentDiagnostic()
        self.verificateur = Verificateur()
        self.interface = InterfaceUtilisateur()
        # Mémoire améliorée
        self.memory = MemoryManager()

        # Profil utilisateur intelligent  
        self.user_profile = UserProfile(self.client)

        # Lier profil à mémoire
        self.memory.user_profile = self.user_profile
        
        # Initialize action modules
        self.gui = GUIController() if GUIController else None
        self.files = FileManager() if FileManager else None
        self.apps = AppLauncher() if AppLauncher else None
        self.cua = None  # Lazy load CUA agent (heavy)
    
    def executer_tache_avec_verification(self, tache):
        for attempt in range(2):
            print(f"🔄 Tentative {attempt + 1}: {tache['description']}")
            
            commande, resultat = self.executer_tache(tache)
            
            if self.verificateur.verifier(tache, resultat):
                return {
                    "status": "success", 
                    "resultat": resultat,
                    "commande_utilisee": commande,
                    "tache_description": tache['description']
                }
            else:
                diagnostic = self.diagnostic.analyser_erreur_systeme(tache['description'], resultat)
                print(f"❌ Blocage: {diagnostic}")
                
                if self.analyse_necessite_utilisateur(diagnostic):
                    resolution = self.demander_intervention_utilisateur(tache, diagnostic, resultat)
                    if resolution.get("resolu"):
                        commande, nouveau_resultat = self.executer_tache(tache)
                        if self.verificateur.verifier(tache, nouveau_resultat):
                            return {
                                "status": "success", 
                                "resultat": nouveau_resultat,
                                "commande_utilisee": commande,
                                "tache_description": tache['description']
                            }
                    else:
                        return {
                            "status": "user_intervention_failed", 
                            "erreur": diagnostic,
                            "tache_description": tache['description']
                        }
                else:
                    if self.resoudre_blocage(diagnostic, tache):
                        continue
        
        return {
            "status": "failed", 
            "erreur": "Échec après tentatives",
            "tache_description": tache['description']
        }
    
    def executer_tache(self, tache):
        """Exécute une tâche en choisissant la meilleure méthode"""
        description = tache['description']
        task_type = tache.get('type')
        
        # ✅ Route 1 : ACTION_SIMPLE → Commande Windows directe
        if task_type == 'action_simple':
            print(f"⚡ Action simple: {description}")
            return self._execute_simple_command(description)
        
        # ✅ Route 2 : ACTION_COMPLEXE → TaskOrchestrator
        if task_type in ['action_complexe', 'cua_complex']:
            print(f"🤖 Tâche complexe: {description}")
            return self.execute_with_orchestrator(description)
        
        # ✅ Route 3 : CONVERSATION / QUESTION_MEMOIRE → Réponse contextuelle
        print(f"💬 Conversation: {description}")
        return self._generer_reponse_conversationnelle(description)
    
    def _execute_simple_command(self, description: str):
        """Exécute une action simple en routant vers le bon outil"""
        
        # Demander au LLM de classifier l'action
        classify_prompt = f"""Tâche: {description}

    Quelle catégorie d'action ?

    1. LAUNCH_APP - Lancer une application desktop (Spotify, Chrome, Discord, etc.)
    2. SYSTEM_CONTROL - Contrôle système (volume, pause, play, screenshot, etc.)
    3. OPEN_FILE - Ouvrir fichier ou URL

Pour SYSTEM_CONTROL, identifie l'action précise parmi:
- Volume: volume_up, volume_down, volume_mute
- Média: play, pause, next, previous, stop
- Fenêtres: close_window, minimize, maximize, switch_window
- Raccourcis: copy, paste, select_all, undo, save
- Capture: screenshot
- "Ouvre le dossier Documents" → {{"category": "OPEN_FILE", "target": "%USERPROFILE%\\Documents"}}
- "Ouvre notes.txt sur le bureau" → {{"category": "OPEN_FILE", "target": "%USERPROFILE%\\Desktop\\notes.txt"}}

    Retourne UNIQUEMENT un JSON:
    {{
        "category": "LAUNCH_APP" | "SYSTEM_CONTROL" | "OPEN_FILE",
        "target": "nom de l'app/fichier/action" (ex: "spotify", "volume_down", "https://url.com")
    }}

    Exemples:
    - "Lance Spotify" → {{"category": "LAUNCH_APP", "target": "spotify"}}
    - "Monte le volume" → {{"category": "SYSTEM_CONTROL", "target": "volume_up"}}
    - "Mute" → {{"category": "SYSTEM_CONTROL", "target": "volume_mute"}}
    - "Musique suivante" → {{"category": "SYSTEM_CONTROL", "target": "next"}}
    - "Ferme la fenêtre" → {{"category": "SYSTEM_CONTROL", "target": "close_window"}}
    - "Pause" → {{"category": "SYSTEM_CONTROL", "target": "pause"}}
    - "Ouvre Chrome" → {{"category": "LAUNCH_APP", "target": "chrome"}}
    - "Ouvre le dossier Documents" → {{"category": "OPEN_FILE", "target": "%USERPROFILE%\\Documents"}}
    - "Ouvre notes.txt sur le bureau" → {{"category": "OPEN_FILE", "target": "%USERPROFILE%\\Desktop\\notes.txt"}}
    - "Ouvre https://youtube.com" → {{"category": "OPEN_FILE", "target": "https://youtube.com"}}
    """
        
        try:
            response = self.client.generate(classify_prompt, max_tokens=100, temperature=0.0).strip()
            # Parser JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)

            # Nettoyer les backslashes si le LLM en a mis
            if json_match:
                json_str = json_match.group()
                # Remplacer \ par / dans les chemins
                json_str = json_str.replace("\\\\", "/").replace("\\", "/")
                decision = json.loads(json_str)
            else:
                # Fallback si pas de match
                response_clean = response.replace("\\\\", "/").replace("\\", "/")
                decision = json.loads(response_clean)
            
            category = decision.get("category")
            target = decision.get("target", "")
            # ✅ DEBUG : Voir ce que le LLM a généré
            print(f"[DEBUG] LLM a généré → category: {category}, target: {target}")
            # Router vers le bon outil
            if category == "LAUNCH_APP":
                # Utiliser AppLauncher (plus fiable)
                if not self.apps:
                    from actions.app_launcher import AppLauncher
                    self.apps = AppLauncher()
                
                result = self.apps.launch_app(target)
                self.memory.sauvegarder_interaction(description, f"App lancée: {target}")
                return "response", f"✅ {target} lancé"
            
            elif category == "SYSTEM_CONTROL":
                # Utiliser GUIController
                if not self.gui:
                    from actions.gui_controller import GUIController
                    self.gui = GUIController()
                
                # ✅ MAPPING COMPLET de toutes les actions système
                action_map = {
                    # Volume
                    "volume_up": lambda: self.gui.press_key("volumeup"),
                    "volume_down": lambda: self.gui.press_key("volumedown"),
                    "volume_mute": lambda: self.gui.press_key("volumemute"),
                    "mute": lambda: self.gui.press_key("volumemute"),
                    
                    # Contrôles média
                    "play": lambda: self.gui.press_key("playpause"),
                    "pause": lambda: self.gui.press_key("playpause"),
                    "stop": lambda: self.gui.press_key("stop"),
                    "next": lambda: self.gui.press_key("nexttrack"),
                    "previous": lambda: self.gui.press_key("prevtrack"),
                    "prev": lambda: self.gui.press_key("prevtrack"),
                    
                    # Raccourcis clavier
                    "copy": lambda: self.gui.copy_to_clipboard(),
                    "paste": lambda: self.gui.paste_from_clipboard(),
                    "select_all": lambda: self.gui.select_all(),
                    "undo": lambda: self.gui.undo(),
                    "save": lambda: self.gui.save(),
                    
                    # Gestion fenêtres
                    "close_window": lambda: self.gui.close_window(),
                    "minimize": lambda: self.gui.minimize_window(),
                    "maximize": lambda: self.gui.maximize_window(),
                    "switch_window": lambda: self.gui.switch_window(),
                    
                    # Capture
                    "screenshot": lambda: self.gui.take_screenshot(),
                }
                
                action_key = target.lower().replace(" ", "_")
                if action_key in action_map:
                    action_map[action_key]()
                    self.memory.sauvegarder_interaction(description, f"Action système: {target}")
                    return "response", f"✅ {description} - Exécuté"
                else:
                    return "response", f"❌ Action système '{target}' non reconnue"
            
            elif category == "OPEN_FILE":
                # Commande Windows simple pour fichiers/URLs/dossiers
                import subprocess
                import os
                
                if target.startswith("http"):
                    # URL
                    subprocess.Popen(f"start {target}", shell=True)
                    msg = f"✅ URL ouverte : {target}"
                else:
                    # Fichier ou dossier local
                    # Détecter si c'est un fichier (a une extension) ou un dossier
                    _, ext = os.path.splitext(target)
                    
                    if ext:  # C'est un fichier (a une extension .txt, .pdf, etc.)
                        # Utiliser 'start' pour ouvrir avec l'application par défaut
                        subprocess.Popen(f"start \"\" \"{target}\"", shell=True)
                        msg = f"✅ Fichier ouvert : {target}"
                    else:  # C'est un dossier
                        # Utiliser 'explorer' pour ouvrir le dossier
                        subprocess.Popen(f"explorer \"{target}\"", shell=True)
                        msg = f"✅ Dossier ouvert : {target}"
                
                self.memory.sauvegarder_interaction(description, f"Ouvert: {target}")
                return "response", msg
            
            else:
                return "response", f"❌ Catégorie '{category}' inconnue"
        
        except Exception as e:
            print(f"[Executeur] Erreur action simple: {e}")
            return "response", f"❌ Erreur: {e}"
    
    
    def _generer_reponse_conversationnelle(self, description: str):
        """Génère une réponse conversationnelle avec contexte"""
        
        # Récupérer contexte et profil
        context = self.memory.get_contexte_recent(description)
        profile_info = self.user_profile.get_contextual_information(description)
        
        reponse_prompt = f"""Question: {description}

    CONTEXTE:
    {context}

    PROFIL:
    {profile_info}

    Réponds de manière naturelle et adaptée au contexte/profil."""
        
        try:
            reponse = self.client.generate(reponse_prompt, max_tokens=300)
            
            # Sauvegarder interaction
            self.memory.sauvegarder_interaction(description, reponse)
            self.user_profile.update_from_interaction(description, reponse)
            
            return reponse
        except Exception as e:
            print(f"[Executeur] Erreur réponse: {e}")
            return self.client.generate(f"Question: {description}\nRéponds de manière concise.")

    def execute_with_orchestrator(self, description: str) -> str:
        """Délègue à l'orchestrateur pour tâches complexes multi-skills"""
        
        # Lazy load orchestrateur
        if not hasattr(self, 'orchestrator'):
            from .task_orchestrator import TaskOrchestrator
            self.orchestrator = TaskOrchestrator(self.client)
            print("[Executeur] Orchestrateur chargé")
        
        # Exécuter la tâche
        result = self.orchestrator.execute_task(description)
        
        if result.get("success", False):
            # LLM décide comment répondre à l'utilisateur
            # ✅ ICI aussi on utilise contexte car on parle
            context = self.memory.get_contexte_recent(description)
            profile_tone = self.user_profile.get_tone_preference()

            prompt = f"""Tâche demandée: {description}

            Résumé de ce qui a été fait: {result['summary']}

            CONTEXTE:
            {context}

            TON PRÉFÉRÉ USER: {profile_tone}

            Génère une réponse NATURELLE et CONCISE pour l'utilisateur.
            Adapte le ton selon le profil."""
            
            try:
                response = self.client.generate(prompt, max_tokens=150, temperature=0.5)

                # Sauvegarder interaction
                self.memory.sauvegarder_interaction(description, response)
                self.user_profile.update_from_interaction(description, response)

                return response.strip()
            except Exception as e:
                return f"✅ Tâche accomplie ! {result['summary']}"
        else:
            error = result.get("error", "Erreur inconnue")
            return f"❌ Désolé, je n'ai pas pu terminer la tâche: {error}"

        
    def shutdown(self):
        """Appelé à la fermeture - consolide la session"""
        
        print("\n[Session] Consolidation en cours...")
        summary = self.memory.consolidate_session()
        
        if summary:
            print(f"[Session] Résumé: {summary}")
        
        print("[Session] Session sauvegardée.")
    
    def analyse_necessite_utilisateur(self, diagnostic):
        prompt = f"""
        Diagnostic: {diagnostic}
        
        Ce problème nécessite-t-il une intervention manuelle de l'utilisateur?
        (ex: mot de passe, permission, choix interactif)
        
        Réponds uniquement par OUI ou NON.
        """
        return self.client.generate(prompt).strip().upper() == "OUI"
    
    def resoudre_blocage(self, diagnostic, tache):
        prompt = f"""
        Problème: {diagnostic}
        Tâche originale: {tache['description']}
        
        Génère une commande de correction SIMPLE.
        Si aucune solution automatique, réponds "INTERVENTION_UTILISATEUR".
        
        Retourne uniquement la commande ou "INTERVENTION_UTILISATEUR".
        """
        
        solution = self.client.generate(prompt).strip()
        if solution != "INTERVENTION_UTILISATEUR":
            print(f"🛠️  Tentative de correction: {solution}")
            resultat = self.executer_commande(solution)
            return self.verificateur.verifier(tache, resultat)
        
        return False
    
    def demander_intervention_utilisateur(self, tache, diagnostic, erreur):
        self.interface.afficher_alerte_blocage(tache['description'], diagnostic, erreur)
        
        suggestions = self.generer_suggestions_resolution(tache, diagnostic)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        print(f"  {len(suggestions) + 1}. Ignorer cette tâche")
        print(f"  {len(suggestions) + 2}. Arrêter l'exécution")
        
        while True:
            try:
                choix = input(f"🎯 Votre choix (1-{len(suggestions) + 2}): ").strip()
                if choix.isdigit():
                    choix_int = int(choix)
                    if 1 <= choix_int <= len(suggestions):
                        print("👤 Résolvez le problème puis appuyez sur Entrée...")
                        input()
                        return {"resolu": True}
                    elif choix_int == len(suggestions) + 1:
                        return {"resolu": False}
                    elif choix_int == len(suggestions) + 2:
                        print("🛑 Arrêt demandé par l'utilisateur")
                        exit(0)
            except KeyboardInterrupt:
                exit(0)
    
    def generer_suggestions_resolution(self, tache, diagnostic):
        prompt = f"""
        Tâche: {tache['description']}
        Problème: {diagnostic}
        
        Génère 3 suggestions pratiques pour résoudre ce problème.
        Chaque suggestion doit être une action concrète.
        
        Format:
        - [Suggestion 1]
        - [Suggestion 2] 
        - [Suggestion 3]
        """
        reponse = self.client.generate(prompt)
        return [line.strip('- ').strip() for line in reponse.split('\n') if line.strip().startswith('-')]
