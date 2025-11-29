"""
CUA Agent - Computer Use Agent Autonome avec Architecture Dual-VLM + OmniParser
Architecture: VLM #1 (Planificateur) ↔ VLM #2 (Exécuteur) avec Feedback Loop
Pipeline: Screenshot → VLM #1 → OmniParser + PaddleOCR + SemanticEnricher →
          Annotation → VLM #2 → PyAutoGUI
"""
import time
import base64
import pyautogui
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List

from .gui_controller import GUIController
from .file_manager import FileManager
from .app_launcher import AppLauncher
from utils.ollama_client import OllamaClient
from config import WEB_SCREENSHOTS_DIR

# Modules de vision
from .vision_preprocessing import preprocessor
from .omniparser_detector import omniparser
from .screen_monitor import screen_monitor
from .visual_annotator import annotator

# OCR Paddle
from .paddle_ocr_detector import paddle_ocr

# Semantic Enricher
from .semantic_enricher import semantic_enricher

# WebHelper (Playwright) + PlaywrightRouter
try:
    from .web_helper import WebHelper
    from .playwright_router import PlaywrightRouter
    from .keyboard_controller import CUAKeyboardController
    from .user_intervention_detector import UserInterventionDetector
    WEBHELPER_AVAILABLE = True
except ImportError:
    WebHelper = None
    PlaywrightRouter = None
    WEBHELPER_AVAILABLE = False


class CUAAgent:
    """
    Agent autonome avec architecture Dual-VLM + OmniParser + PaddleOCR:
    - VLM #1: Planification et vérification haut niveau
    - VLM #2: Exécution précise avec visual grounding
    - OmniParser: UI Detection + Semantic Caption
    - PaddleOCR: Texte
    - SemanticEnricher: Fusion OCR + OmniParser et description enrichie
    """

    def __init__(self, vlm_model=None):
        """Initialise l'agent CUA avec pipeline vision OmniParser + PaddleOCR"""
        from config import TARS_MODEL_NAME, FALLBACK_VLM_MODEL

        self.gui = GUIController()
        self.files = FileManager()
        self.apps = AppLauncher()
        self.llm = OllamaClient()
        # WebHelper (Playwright) - fail-safe
        from config import ENABLE_PLAYWRIGHT_SUPPORT, CHROME_DEBUG_PORT
        
        self.web = None
        self.router = None  # PlaywrightRouter pour fast-path
        if ENABLE_PLAYWRIGHT_SUPPORT and WEBHELPER_AVAILABLE:
            try:
                self.web = WebHelper(debug_port=CHROME_DEBUG_PORT)
                if self.web and self.web.connected:
                    self.router = PlaywrightRouter(self.web)
                    print("[CUA] PlaywrightRouter activé (fast-path)")
            except Exception as e:
                print(f"[CUA] WebHelper indisponible: {e}")
        # Détecteur d'intervention utilisateur
        from config import ENABLE_USER_INTERVENTION_DETECTION, USER_INTERVENTION_VLM_VALIDATION
        self.intervention_detector = None
        if ENABLE_USER_INTERVENTION_DETECTION:
            self.intervention_detector = UserInterventionDetector(
                use_vlm_validation=USER_INTERVENTION_VLM_VALIDATION
            )
        # VLM #1 (Planification) - utilise FALLBACK_VLM_MODEL (qwen2.5vl)
        # VLM #2 (Exécution) - utilise TARS_MODEL_NAME (qwen3-vl:4b)
        if vlm_model is None:
            try:
                print(f"[CUA] Initialisation VLM #1 (planification): {FALLBACK_VLM_MODEL}")
                self.vlm1 = OllamaClient(model=FALLBACK_VLM_MODEL)
                print("[CUA] VLM #1 chargé ✓")
            except Exception as e:
                print(f"[CUA] Erreur VLM #1: {e}")
                self.vlm1 = None
            
            try:
                print(f"[CUA] Initialisation VLM #2 (exécution): {TARS_MODEL_NAME}")
                self.vlm2 = OllamaClient(model=TARS_MODEL_NAME)
                print("[CUA] VLM #2 chargé ✓")
            except Exception as e:
                print(f"[CUA] Erreur VLM #2: {e}")
                self.vlm2 = None
            
            # Rétrocompatibilité
            self.vlm = self.vlm2 if self.vlm2 else self.vlm1
            self.vlm_model = TARS_MODEL_NAME if self.vlm2 else FALLBACK_VLM_MODEL
        else:
            # Mode manuel : même modèle pour les deux
            self.vlm_model = vlm_model
            self.vlm1 = OllamaClient(model=vlm_model)
            self.vlm2 = OllamaClient(model=vlm_model)
            self.vlm = self.vlm1

        self.screenshots_dir = Path(WEB_SCREENSHOTS_DIR)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        self.action_history: List[Dict] = []
        self.max_iterations = 50

        print("[CUA] Agent prêt (Dual-VLM + OmniParser + PaddleOCR + SemanticEnricher)")

    def execute_task(self, task_description: str, max_steps: int = 30) -> Dict:
        """
        Exécute une tâche de manière autonome avec architecture Dual-VLM + OmniParser + PaddleOCR

        Pipeline:
        1. Screenshot
        2. VLM #1: Planification + Vérification
        3. Vision: OmniParser (UI Detection + Caption) + PaddleOCR (texte)
        4. SemanticEnricher: fusion + description enrichie
        5. Annotation visuelle (Set-of-Mark)
        6. VLM #2: Exécution avec visual grounding
        7. PyAutoGUI: Actions (+ séquences)
        8. Feedback → VLM #1
        """
        print(f"\n[CUA] Tâche: {task_description}")
        print("=" * 60)

        self.action_history = []
        screen_monitor.reset_history()
        step = 0
        task_completed = False

        context: Dict = {
            "task": task_description,
            "steps_done": [],
            "current_state": "initial",
            "last_action_result": "Aucune action précédente",
            "current_url": "Inconnue",  # ← NOUVEAU
        }

        # Keyboard controller pour touches P/C/Q
        from config import ENABLE_KEYBOARD_CONTROL
        keyboard_ctrl = None
        if ENABLE_KEYBOARD_CONTROL:
            try:
                keyboard_ctrl = CUAKeyboardController()
                print("\n[CUA] Touches disponibles: [P] Pause | [C] Continue | [Q] Quit")
            except Exception as e:
                print(f"[CUA] Keyboard control désactivé: {e}")

        while step < max_steps and not task_completed:
            # Vérifier arrêt utilisateur
            if keyboard_ctrl and keyboard_ctrl.stop_requested:
                print("\n[CUA] Arrêt demandé par l'utilisateur")
                break
            
            # Vérifier pause manuelle
            if keyboard_ctrl and keyboard_ctrl.paused:
                print("⏸️  En pause - En attente de [C]...")
                while keyboard_ctrl.paused and not keyboard_ctrl.stop_requested:
                    time.sleep(0.5)
                
                if keyboard_ctrl.stop_requested:
                    break
                
                print("▶️  Reprise - Capture nouvel état...")
                time.sleep(1)
                continue
            
            step += 1
            print("\n" + "=" * 60)
            print(f"[CUA] Étape {step}/{max_steps}")
            print("=" * 60 + "\n")
            
            try:
                # 0. WEBHELPER : Préparation (URL + Popups)
                if self.web and self.web.connected:
                    # Rafraîchir la connexion pour la bonne page
                    self.web.refresh_connection()
                    
                    # Récupérer URL actuelle
                    current_url = self.web.get_current_url()
                    if current_url:
                        context["current_url"] = current_url
                        print(f"[WebHelper] URL: {current_url}")
                    
                    # Fermer popups AVANT screenshot (pour une Vision plus propre)
                    from config import AUTO_CLOSE_POPUPS
                    if AUTO_CLOSE_POPUPS and self.web.handle_popups_auto():
                        print("[WebHelper] Popups fermés")
                        time.sleep(0.5)  # Laisser le DOM se stabiliser
                
                # 1. SCREENSHOT
                screenshot_path = self.capture_screen(step)
                
                # Vérifier pause manuelle
                if keyboard_ctrl and keyboard_ctrl.paused:
                    print("⏸️  En pause - En attente de [C]...")
                    while keyboard_ctrl.paused and not keyboard_ctrl.stop_requested:
                        time.sleep(0.5)
                    
                    if keyboard_ctrl.stop_requested:
                        break
                    
                    print("▶️  Reprise - Capture nouvel état...")
                    time.sleep(1)
                    continue

                # 2. PREPROCESSING
                original_img = cv2.imread(str(screenshot_path))
                # --- AJOUT: CROP PARTIE DROITE ---
                # Exemple: on garde 70% de la largeur (de 0 à 70%)
                h, w = original_img.shape[:2]
                new_width = int(w * 0.70)  # <--- Change 0.70 selon tes besoins
                original_img = original_img[0:h, 0:new_width]
                
                # CRITIQUE: On écrase le fichier pour que tout le pipeline utilise le crop
                cv2.imwrite(str(screenshot_path), original_img)
                if original_img is None:
                    print(f"[CUA] Impossible de lire le screenshot: {screenshot_path}")
                    break

                original_h, original_w = original_img.shape[:2]

                preprocessed = self.preprocess_screenshot(screenshot_path)
                preprocessed_path = self.screenshots_dir / f"preprocessed_step_{step}.png"
                cv2.imwrite(str(preprocessed_path), preprocessed)

                preprocessed_h, preprocessed_w = preprocessed.shape[:2]

                scale_x = original_w / float(preprocessed_w)
                scale_y = original_h / float(preprocessed_h)
                context["scale_factor"] = (scale_x, scale_y)
                print(
                    f"[CUA] Scale: {original_w}x{original_h} → {preprocessed_w}x{preprocessed_h} "
                    f"(x{scale_x:.2f}, y{scale_y:.2f})"
                )

                # 3. VLM #1 - PLANIFICATION / CHECK TÂCHE
                vlm_plan = self.analyze_with_vlm(screenshot_path, context)
                # Vérifier pause manuelle
                if keyboard_ctrl and keyboard_ctrl.paused:
                    print("⏸️  En pause - En attente de [C]...")
                    while keyboard_ctrl.paused and not keyboard_ctrl.stop_requested:
                        time.sleep(0.5)
                    if keyboard_ctrl.stop_requested:
                        break
                    print("▶️  Reprise - Capture nouvel état...")
                    time.sleep(1)
                    continue
                vlm_description = vlm_plan.get("description", "Écran visible")
                vlm_suggestion = vlm_plan.get("suggestion", "Continuer")
                task_complete = vlm_plan.get("task_complete", False)
                # Décharger VLM #1 immédiatement pour libérer VRAM
                self.vlm1.unload()
                if task_complete:
                    print(f"\n[CUA] VLM #1 confirme: tâche terminée en {step} étapes")
                    task_completed = True
                    break

                # 3.5 PLAYWRIGHT FAST-PATH (NOUVEAU)
                # Tenter d'exécuter via Playwright AVANT le pipeline Vision
                if self.router:
                    print(f"\n[CUA] 🚀 Tentative fast-path Playwright...")
                    print(f"[CUA] Suggestion VLM #1: '{vlm_suggestion}'")
                    
                    try:
                        if self.router.try_fast_path(vlm_suggestion, task_description):
                            print("[CUA] ✅ Fast-path réussi ! Skip Vision pipeline")
                            
                            # Mettre à jour le contexte
                            context["last_action_result"] = f"Fast-path Playwright: {vlm_suggestion} - SUCCÈS"
                            context["steps_done"].append(f"Playwright: {vlm_suggestion}")
                            
                            self.action_history.append({
                                "step": step,
                                "vlm_plan": vlm_plan,
                                "fast_path": True,
                                "action": {"action": "playwright", "suggestion": vlm_suggestion},
                                "result": "Succès via Playwright",
                            })
                            
                            time.sleep(2)
                            
                            # ✅ NOUVEAU : Vérifier si tâche globale terminée
                            step += 1
                            new_screenshot = self.capture_screen(step)
                            check_plan = self.analyze_with_vlm(new_screenshot, context)
                            
                            if check_plan.get("task_complete"):
                                print("[CUA] ✅ Playwright + VLM confirment: tâche terminée")
                                task_completed = True
                                break
                            else:
                                print("[CUA] Playwright OK, mais tâche pas terminée → Continue")
                                continue
                        else:
                            print("[CUA] ⚠️ Fast-path échec → Fallback Vision pipeline")
                    except Exception as e:
                        print(f"[CUA] ⚠️ Erreur fast-path: {e} → Fallback Vision pipeline")
                        import traceback
                        traceback.print_exc()

                # Si on arrive ici: soit pas de router, soit fast-path a échoué
                # → Continuer avec le pipeline Vision normal

                # 4. VISION: OmniParser + PaddleOCR + SemanticEnricher
                print("\n[CUA] Vision: OmniParser + PaddleOCR + SemanticEnricher")

                # 4.1 OmniParser
                omni_clickables = omniparser.detect_ui_elements(preprocessed)
                print(
                    f"[CUA] OmniParser: {len(omni_clickables)} éléments UI bruts détectés"
                )

                # 4.2 PaddleOCR sur l'image préprocessée (même repère que OmniParser)
                ocr_results = paddle_ocr.detect_text(preprocessed)
                print(f"[CUA] PaddleOCR: {len(ocr_results)} textes détectés")

                # 4.3 SemanticEnricher: fusion OCR + OmniParser, classification fonctionnelle
                enriched_clickables = semantic_enricher.enrich(
                    clickable_elements=omni_clickables,
                    ocr_results=ocr_results,
                    image_shape=preprocessed.shape[:2],
                    context="browser",
                )
                clickables_text = semantic_enricher.format_for_llm(enriched_clickables)

                # 4.4 AJOUT : Tous les textes OCR comme éléments cliquables séparés
                # (même si déjà dans une box OmniParser - le VLM choisira la précision)
                ocr_elements = []
                symboles_communs = ['×', '+', '−', '—', '←', '→', '↑', '↓', '☰', '⋮', '•', '*', '.', ',', '!', '?', 'x', 'X']
                
                for ocr in ocr_results:
                    ocr_text = ocr.get('text', '').strip()
                    
                    # Ignorer symboles simples (déjà détectés par OmniParser)
                    if ocr_text in symboles_communs:
                        continue
                    
                    # Ignorer textes vides ou trop courts (< 2 caractères) sauf chiffres
                    if len(ocr_text) < 1 or (len(ocr_text) == 1 and not ocr_text.isdigit()):
                        continue
                    
                    ocr_elem = {
                        'id': len(enriched_clickables) + len(ocr_elements),
                        'label': ocr_text,
                        'description': f"Text: {ocr_text}",
                        'bbox': ocr.get('bbox', [0, 0, 0, 0]),
                        'center': ocr.get('center', (0, 0)),
                        'confidence': ocr.get('confidence', 0.0),
                        'type': 'text_ocr',  # Pour distinction visuelle (couleur cyan)
                        'enriched_description': f"Text: {ocr_text}",
                        'visual_description': 'Text element',
                        'ocr_nearby': ocr_text,
                        'functional_type': 'text',
                        'function': 'text',
                        'spatial_context': 'main content',
                        'position': list(ocr.get('center', (0, 0))),
                    }
                    ocr_elements.append(ocr_elem)
                
                symboles_ignores = len([t for t in ocr_results if t.get('text','').strip() in symboles_communs])
                print(f"[CUA] Ajout {len(ocr_elements)} textes OCR (ignoré {symboles_ignores} symboles)")
                
                # Combiner OmniParser enrichis + Textes OCR
                enriched_clickables = enriched_clickables + ocr_elements
                
                # Réassigner IDs séquentiels pour cohérence
                for i, elem in enumerate(enriched_clickables):
                    elem['id'] = i
                
                # Reformater pour VLM avec éléments combinés
                clickables_text = semantic_enricher.format_for_llm(enriched_clickables)

                # 5. ANNOTATION VISUELLE (Set-of-Mark) avec éléments enrichis + OCR
                annotated_screenshot = annotator.annotate_screenshot(
                    preprocessed_path,
                    enriched_clickables,
                )
                print(f"[CUA] Screenshot annoté: {annotated_screenshot}")

                # 6. SCREEN MONITORING
                image = original_img
                change_report = screen_monitor.add_frame(image)
                change_summary = screen_monitor.get_change_summary()
                if change_report.get("changed"):
                    print(
                        f"[CUA] Changement détecté: {change_report.get('change_type')}"
                    )
                # Vérifier pause manuelle
                if keyboard_ctrl and keyboard_ctrl.paused:
                    print("⏸️  En pause - En attente de [C]...")
                    while keyboard_ctrl.paused and not keyboard_ctrl.stop_requested:
                        time.sleep(0.5)
                    if keyboard_ctrl.stop_requested:
                        break
                    print("▶️  Reprise - Capture nouvel état...")
                    time.sleep(1)
                    continue
                # 7. VLM #2 - EXÉCUTION AVEC VISUAL GROUNDING
                next_action = self.plan_next_action(
                    task_description,
                    vlm_description,
                    vlm_suggestion,
                    clickables_text,
                    change_summary,
                    context,
                    annotated_screenshot,
                )
                # Vérifier pause manuelle
                if keyboard_ctrl and keyboard_ctrl.paused:
                    print("⏸️  En pause - En attente de [C]...")
                    while keyboard_ctrl.paused and not keyboard_ctrl.stop_requested:
                        time.sleep(0.5)
                    if keyboard_ctrl.stop_requested:
                        break
                    print("▶️  Reprise - Capture nouvel état...")
                    time.sleep(1)
                    continue
                print(f"[CUA] VLM #2 action proposée: {next_action}")
                
                # ✅ NOUVEAU BLOC ICI
                if self.intervention_detector:
                    page_text = self.web.get_page_text() if self.web else ""
                    intervention = self.intervention_detector.detect_intervention_needed(
                        screenshot_path=str(screenshot_path),
                        page_text=page_text,
                        vlm_description=vlm_description,
                        planned_action=next_action  # ✅ DICT maintenant
                    )

                    if intervention["needed"]:
                        print(f"\n⏸  INTERVENTION REQUISE: {intervention['reason']}")
                        print(f"    {intervention['message']}")
                        input("\n👤 Appuyez sur Entrée après intervention...")
                        time.sleep(1)
                        continue

                # 8. EXÉCUTION (avec support séquences + scale correction)
                action_result = self.execute_action(
                    next_action,
                    enriched_clickables,
                    context.get("scale_factor", (1.0, 1.0)),
                )
                # Vérifier pause manuelle
                if keyboard_ctrl and keyboard_ctrl.paused:
                    print("⏸️  En pause - En attente de [C]...")
                    while keyboard_ctrl.paused and not keyboard_ctrl.stop_requested:
                        time.sleep(0.5)
                    if keyboard_ctrl.stop_requested:
                        break
                    print("▶️  Reprise - Capture nouvel état...")
                    time.sleep(1)
                    continue
                print(f"[CUA] Résultat exécution: {action_result}")

                # 9. FEEDBACK pour VLM #1
                action_description = next_action.get(
                    "reasoning", "Action exécutée"
                )
                context["last_action_result"] = (
                    f"{action_description} - Résultat: {action_result}"
                )

                self.action_history.append(
                    {
                        "step": step,
                        "vlm_plan": vlm_plan,
                        "clickables_count": len(enriched_clickables),
                        "action": next_action,
                        "result": action_result,
                        "task_complete": task_completed,
                    }
                )
                context["steps_done"].append(action_description)

                time.sleep(2)

            except Exception as e:
                print(f"[CUA] Erreur étape {step}: {e}")
                import traceback
                traceback.print_exc()

                if step < max_steps - 1:
                    print("[CUA] Tentative de récupération...")
                    continue
                else:
                    break

        return {
            "status": "success" if task_completed else "partial",
            "steps": step,
            "task": task_description,
            "history": self.action_history,
            "completed": task_completed,
            "task_complete": task_completed, 
        }

    def capture_screen(self, step: int) -> Path:
        """Capture screenshot"""
        return self.gui.take_screenshot(f"cua_step_{step}.png")

    def preprocess_screenshot(self, screenshot_path: Path) -> np.ndarray:
        """Preprocessing OpenCV"""
        return preprocessor.preprocess_from_path(screenshot_path)

    def analyze_with_vlm(self, screenshot_path: Path, context: Dict) -> Dict:
        """
        VLM #1: Planification et vérification (utilise qwen2.5vl via FALLBACK_VLM_MODEL)

        Retourne:
        {
            'description': str,
            'suggestion': str,
            'task_complete': bool
        }
        """
        if self.vlm1 is None:
            return {
                "description": "Écran visible",
                "suggestion": "Continuer",
                "task_complete": False,
            }

        try:
            with open(screenshot_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            last_action = context.get(
                "last_action_result", "Aucune action précédente"
            )

            steps_done = context.get("steps_done", [])
            if steps_done:
                steps_text = "\n".join(f"- {s}" for s in steps_done[-3:])
            else:
                steps_text = "- Aucune"

            current_url = context.get("current_url", "Inconnue")
            
            prompt = f"""Tu es un planificateur intelligent pour un agent d'automatisation.

TÂCHE GLOBALE: {context['task']}
URL ACTUELLE: {current_url}

ACTION PRÉCÉDENTE: {last_action}

ÉTAPES DÉJÀ ACCOMPLIES:
{steps_text}

REGARDE L'IMAGE et réponds en JSON:

1. "description": Décris brièvement ce que tu vois (application, état, éléments principaux)
2. "suggestion": Quelle action faire MAINTENANT pour progresser vers la tâche ? (langage naturel, générique)
3. "task_complete": true si la tâche globale est complètement terminée, false sinon

NE JAMAIS mentionner d'IDs ou de coordonnées - seulement des descriptions.

RÉPONDS UNIQUEMENT en JSON valide:
{{
    "description": "...",
    "suggestion": "...",
    "task_complete": true/false
}}"""

            response = self.vlm1.generate_with_image(prompt, image_data)

            import json
            import re

            match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response, re.DOTALL)
            if match:
                result = json.loads(match.group())
                print("[CUA] VLM #1 planificateur:")
                print(
                    f"  Description: {result.get('description', '')[:100]}..."
                )
                print(f"  Suggestion: {result.get('suggestion', '')}")
                print(
                    f"  Tâche complète: {result.get('task_complete', False)}"
                )
                self.vlm1.unload() 
                return result
            else:
                self.vlm1.unload() 
                return {
                    "description": response[:200],
                    "suggestion": "Continuer",
                    "task_complete": False,
                }
        except Exception as e:
            print(f"[CUA] Erreur VLM #1: {e}")
            import traceback
            traceback.print_exc()
            
            self.vlm1.unload() 
            return {
                "description": "Écran visible",
                "suggestion": "Continuer",
                "task_complete": False,
            }

    def determine_zone_with_llm(self, task: str, vlm_suggestion: str) -> str:
        """
        LLM détermine quelle zone scanner (parmi 4 choix)
        """
        prompt = f"""Tu localises des éléments dans une interface web.

4 ZONES DISPONIBLES:
1. browser_toolbar - Onglets navigateur, navigation, URL, extensions
3. content - Menu du site, barre recherche, Contenu principal de la page
4. footer - Bas de page, pagination

TÂCHE: {task}
SUGGESTION: {vlm_suggestion}

Réponds UNIQUEMENT avec le nom de la zone (1 mot):"""

        try:
            response = self.llm.generate(prompt)
            zone = response.strip().lower()
            
            # Validation
            if zone in ["browser_toolbar", "content", "footer"]:
                print(f"[CUA] Zone déterminée: {zone}")
                self.llm.unload()  # ← AJOUTER ICI
                return zone
            else:
                print(f"[CUA] Zone invalide '{zone}', fallback: content")
                self.llm.unload()  # ← AJOUTER ICI AUSSI
                return "content"
        except Exception as e:
            print(f"[CUA] Erreur détermination zone: {e}")
            self.llm.unload()  # ← OK vous l'avez déjà
            return "content"

    def crop_annotated_image(self, image_path: Path, zone: str) -> Path:
        """
        Découpe l'image annotée selon la zone déterminée par le LLM
        Retourne le chemin de l'image croppée
        """
        # Lire l'image annotée
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"[CUA] Erreur lecture image: {image_path}")
            return image_path
        
        h, w = img.shape[:2]
        
        # Définir les zones (en pourcentage de hauteur)
        ZONES = {
            "browser_toolbar": (0, 0, w, int(h * 0.15)),
            "content": (0, int(h * 0.10), w, int(h * 0.90)),
            "footer": (0, int(h * 0.90), w, h)
        }
        
        x1, y1, x2, y2 = ZONES.get(zone, (0, 0, w, h))
        cropped = img[y1:y2, x1:x2]
        
        # Sauvegarder l'image croppée
        cropped_path = image_path.parent / f"cropped_{image_path.name}"
        cv2.imwrite(str(cropped_path), cropped)
        
        percentage = (x2-x1)*(y2-y1)*100/(w*h)
        print(f"[CUA] Image annotée croppée ({zone}): {cropped.shape[1]}x{cropped.shape[0]} ({percentage:.1f}% de l'image)")
        
        return cropped_path

    def plan_next_action(
        self,
        task: str,
        vlm_desc: str,
        vlm_suggestion: str,
        clickables: str,
        changes: str,
        context: Dict,
        annotated_screenshot_path: Path,
    ) -> Dict:
        """
        VLM #2: Exécuteur avec screenshot annoté + suggestion VLM #1
        (utilise qwen3-vl:4b via TARS_MODEL_NAME)

        Le VLM #2 reçoit:
          - la suggestion haut niveau de VLM #1
          - la liste détaillée des éléments cliquables (avec IDs)
          - le screenshot annoté avec les IDs en vert
        """
        print(
            f"\n[CUA] VLM #2 reçoit la suggestion de VLM #1: '{vlm_suggestion}'"
        )

        print("\n[CUA] Liste des éléments envoyés à VLM #2:")
        print(clickables)
        print("=" * 60)

        is_search = any(
            kw in vlm_suggestion.lower()
            for kw in ["chercher", "taper", "rechercher", "saisir"]
        )

        if is_search:
            import re

            match = re.search(r"['\"]([^'\"]+)['\"]", vlm_suggestion)
            search_text = match.group(1) if match else "youtube"

            prompt = f"""REGARDE l'image annotée.

Tu vois des NUMÉROS VERTS sur l'écran, chacun correspond à un élément cliquable.

SUGGESTION HAUT NIVEAU: {vlm_suggestion}


TROUVE le numéro de la BARRE DE RECHERCHE (cherche "Recherch" ou "saisir").

Renvoie UNIQUEMENT un JSON valide de la forme:

{{
  "action": "sequence",
  "params": {{
    "steps": [
      {{"action": "click_on_element", "params": {{"id": ID_BARRE_RECHERCHE}}}},
      {{"action": "type_text", "params": {{"text": "{search_text}"}}}},
      {{"action": "press_key", "params": {{"key": "enter"}}}}
    ]
  }}
}}"""
        else:
            prompt = f"""REGARDE l'image annotée.

Tu vois des NUMÉROS VERTS sur l'écran, chacun correspond à un élément cliquable.

TÂCHE GLOBALE: {task}

SUGGESTION HAUT NIVEAU: {vlm_suggestion}


Choisis le prochain élément à cliquer pour faire progresser la tâche, et renvoie UNIQUEMENT un JSON valide de la forme:

{{
  "action": "click_on_element",
  "params": {{
    "id": ID_A_CLIQUER
  }}
}}"""

        try:
            # Déterminer la zone pertinente avec le LLM
            zone = self.determine_zone_with_llm(task, vlm_suggestion)
            
            # Cropper l'image annotée selon la zone
            cropped_screenshot_path = self.crop_annotated_image(annotated_screenshot_path, zone)
            
            # Lire l'image croppée
            with open(cropped_screenshot_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            print("\n[CUA] Prompt envoyé à VLM #2:")
            print(prompt)
            print("=" * 60)

            response = self.vlm2.generate_with_image(prompt, image_data)

            print("\n[CUA] Réponse brute du VLM #2:")
            print(response)
            print("=" * 60)

            # Vérifier si la réponse est une erreur rapportée par OllamaClient
            if response.startswith("Erreur VLM Ollama:"):
                raise Exception(response)

            import json

            start = response.find("{")
            if start != -1:
                bracket_count = 0
                for i, char in enumerate(response[start:], start=start):
                    if char == "{":
                        bracket_count += 1
                    elif char == "}":
                        bracket_count -= 1
                        if bracket_count == 0:
                            json_str = response[start : i + 1]
                            try:
                                action = json.loads(json_str)
                                print(f"[CUA] VLM #2 JSON parsé: {action}")
                                self.vlm2.unload() 
                                return action
                            except json.JSONDecodeError as e:
                                print(f"[CUA] Erreur parsing JSON: {e}")
                                print(f"[CUA] JSON extrait: {json_str}")
                                self.vlm2.unload() 
                                return {
                                    "action": "wait",
                                    "params": {"seconds": 2},
                                    "reasoning": f"Parse failed: {e}",
                                }

            self.vlm2.unload() 
            return {
                "action": "wait",
                "params": {"seconds": 2},
                "reasoning": "No JSON found",
            }
        except Exception as e:
            error_message = str(e)
            print(f"[CUA] Erreur VLM #2: {error_message}")
            import traceback
            traceback.print_exc()
            self.vlm2.unload() 
            
            # Si timeout ou erreur de connexion, basculer vers VLM #1 (fallback)
            if "timeout" in error_message.lower() or "connection" in error_message.lower():
                print(f"\n[CUA] ⚠️ Timeout détecté sur VLM #2, bascule vers VLM #1 (fallback)...")
                self.vlm2.unload() 
                try:
                    # Réutiliser l'image annotée croppée déjà préparée
                    # et le même prompt - juste changer le modèle
                    with open(cropped_screenshot_path, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode()
                    
                    print("[CUA] Envoi vers VLM #1 (fallback) avec même image annotée croppée...")
                    print(f"[CUA] Prompt identique à VLM #2")
                    
                    fallback_response = self.vlm1.generate_with_image(prompt, image_data)
                    
                    print(f"\n[CUA] Réponse fallback VLM #1:")
                    print(fallback_response)
                    print("=" * 60)
                    
                    # Parser le JSON (même logique que VLM #2)
                    import json
                    start = fallback_response.find("{")
                    if start != -1:
                        bracket_count = 0
                        for i, char in enumerate(fallback_response[start:], start=start):
                            if char == "{":
                                bracket_count += 1
                            elif char == "}":
                                bracket_count -= 1
                                if bracket_count == 0:
                                    json_str = fallback_response[start : i + 1]
                                    try:
                                        action = json.loads(json_str)
                                        print(f"[CUA] ✓ Fallback VLM #1 JSON parsé: {action}")
                                        self.vlm1.unload() 
                                        return action
                                    except json.JSONDecodeError as e:
                                        print(f"[CUA] Erreur parsing fallback JSON: {e}")
                    
                    print("[CUA] ❌ Fallback: aucun JSON trouvé, action wait par défaut")
                    self.vlm1.unload() 
                    return {
                        "action": "wait",
                        "params": {"seconds": 2},
                        "reasoning": "Fallback VLM #1: No JSON found",
                    }
                    
                except Exception as fallback_error:
                    print(f"[CUA] ❌ Erreur lors du fallback VLM #1: {fallback_error}")
                    import traceback
                    traceback.print_exc()
                    self.vlm1.unload() 
                    return {
                        "action": "wait",
                        "params": {"seconds": 2},
                        "reasoning": f"Both VLM #2 and fallback VLM #1 failed",
                    }
            
            # Pour les autres erreurs, retourner wait
            self.vlm2.unload() 
            return {
                "action": "wait",
                "params": {"seconds": 2},
                "reasoning": f"Error: {e}",
            }

    def execute_action(
        self,
        action_dict: Dict,
        clickables: List[Dict],
        scale_factor: tuple = (1.0, 1.0),
    ) -> str:
        """
        Exécute une action avec support des éléments enrichis + séquences + correction de scale
        """
        action = action_dict.get("action")
        params = action_dict.get("params", {})
        scale_x, scale_y = scale_factor

        try:
            if action == "sequence":
                steps = params.get("steps", [])
                results = []
                for step in steps:
                    result = self.execute_action(step, clickables, scale_factor)
                    results.append(result)
                    time.sleep(0.3)
                return " → ".join(results)

            elif action == "click_on_element":
                element_id = params.get("id", 0)
                # Convertir en int si c'est une string (certains VLM retournent des strings)
                element_id = int(element_id) if isinstance(element_id, str) else element_id
                if 0 <= element_id < len(clickables):
                    elem = clickables[element_id]
                    cx, cy = elem.get("center", elem.get("position", (0, 0)))

                    x_real = int(cx * scale_x)
                    y_real = int(cy * scale_y)

                    label = (
                        elem.get("enriched_description")
                        or elem.get("visual_description")
                        or elem.get("description")
                        or elem.get("label")
                        or "element"
                    )

                    self.gui.click(x_real, y_real)
                    return (
                        f"Clique sur '{label}' à ({x_real},{y_real}) "
                        f"[coordonnées préprocessées ({cx},{cy})]"
                    )
                return f"ID invalide: {element_id}"

            elif action == "type_text":
                text = params.get("text", "")
                self.gui.type_text(text)
                return f"Tape le texte: '{text}'"

            elif action == "press_key":
                key = params.get("key", "")
                self.gui.press_key(key)
                return f"Touche pressée: {key}"

            elif action == "hotkey":
                keys = params.get("keys", [])
                if isinstance(keys, str):
                    keys = [keys]
                self.gui.hotkey(*keys)
                return f"Raccourci clavier: {'+'.join(keys)}"

            elif action == "open_url":
                url = params.get("url", "")
                self.apps.launch_url(url)
                return f"URL ouverte: {url}"

            elif action == "scroll":
                clicks = params.get("clicks", -3)
                self.gui.scroll(clicks)
                return f"Scroll: {clicks}"

            elif action == "wait":
                seconds = params.get("seconds", 1)
                time.sleep(seconds)
                return f"Attente de {seconds} secondes"

            return f"Action inconnue: {action}"
        except Exception as e:
            return f"Erreur exécution action: {e}"

    def check_task_completion(
        self, task: str, context: Dict, screenshot_path: Path
    ) -> bool:
        """Vérifie si tâche terminée (délégué à VLM #1 maintenant)"""
        return False


# Pour compatibilité
def get_summary(self) -> str:
    """Résumé simple"""
    return f"Tâche exécutée en {len(self.action_history)} étapes"
