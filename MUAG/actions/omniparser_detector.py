"""
OmniParser Detector Module
Détection d'éléments UI + Caption sémantique avec OmniParser v2.0
Pipeline: icon_detect (YOLOv8) + icon_caption (Florence-2)
FIXED: Eager attention forcé pour Windows (pas de flash_attn)
"""
import cv2
import numpy as np
import time
import torch
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from config import (
    OMNIPARSER_WEIGHTS_DIR,
    OMNIPARSER_DEVICE,
    OMNIPARSER_CONFIDENCE_THRESHOLD
)


class OmniParserDetector:
    """
    Détection UI avec OmniParser v2.0
    Combine détection (YOLOv8) + caption sémantique (Florence-2)
    """
    
    def __init__(self):
        """Initialise OmniParser avec icon_detect + icon_caption"""
        print("[OmniParser] Initialisation OmniParser v2.0...")
        
        self.device = OMNIPARSER_DEVICE
        self.confidence_threshold = OMNIPARSER_CONFIDENCE_THRESHOLD
        
        try:
            # DIAGNOSTIC Flash Attention
            print("[DEBUG] Vérification Flash Attention...")
            try:
                import flash_attn
                print("[WARN]  flash_attn détecté - va être désactivé pour Windows")
                self.has_flash = True
            except ImportError:
                print("[OK]  flash_attn non installé - eager attention sera utilisé")
                self.has_flash = False
            
            # Vérifier que OmniParser est installé
            omni_dir = Path("OmniParser")
            if not omni_dir.exists():
                raise FileNotFoundError(
                    "OmniParser non trouvé. Exécutez: /install_omniparser"
                )
            
            # Charger icon_detect (YOLOv8)
            self._load_icon_detect()
            
            # Charger icon_caption (Florence-2) avec eager attention
            self._load_icon_caption()
            
            print(f"[OK] OmniParser chargé (device: {self.device})")
            
        except Exception as e:
            print(f"[ERROR] Erreur OmniParser: {e}")
            print("   OmniParser désactivé - exécutez /install_omniparser")
            import traceback
            traceback.print_exc()
            self.icon_detect = None
            self.icon_caption = None
    
    def _load_icon_detect(self):
        """Charge le modèle YOLOv8 pour détection d'icônes"""
        from ultralytics import YOLO
        
        model_path = Path("OmniParser/weights/icon_detect/model.pt")
        
        if not model_path.exists():
            raise FileNotFoundError(f"Modèle icon_detect non trouvé: {model_path}")
        
        print(f"[OmniParser] Chargement icon_detect (YOLOv8)...")
        self.icon_detect = YOLO(str(model_path))
        
        # Configurer device
        if self.device == "cuda" and not torch.cuda.is_available():
            print("[WARN] CUDA non disponible, utilisation CPU")
            self.device = "cpu"
        
        print(f"[OK] icon_detect chargé")
    
    def _load_icon_caption(self):
        """Charge le modèle Florence-2 pour caption d'icônes (Windows compatible)"""
        from transformers import AutoModelForCausalLM, AutoProcessor
        
        model_path = Path("OmniParser/weights/icon_caption_florence")
        
        if not model_path.exists():
            raise FileNotFoundError(f"Modèle icon_caption non trouvé: {model_path}")
        
        print(f"[OmniParser] Chargement icon_caption (Florence-2) - Mode Windows...")
        
        self.caption_processor = AutoProcessor.from_pretrained(
            str(model_path),
            trust_remote_code=True
        )
        
        # CRITIQUE : Forcer eager attention + float32 sur Windows
        print(f"[OmniParser] Forçage eager attention (désactivation flash_attn)...")
        
        try:
            self.caption_model = AutoModelForCausalLM.from_pretrained(
                str(model_path),
                trust_remote_code=True,
                torch_dtype=torch.float32,  # Forcer float32 sur Windows
                attn_implementation='eager',  # Forcer eager attention
                use_flash_attention_2=False,  # Désactiver explicitement flash_attn
            )
            
            # PATCH SUPPLÉMENTAIRE : Forcer dans la config
            if hasattr(self.caption_model, 'config'):
                self.caption_model.config._attn_implementation = 'eager'
                self.caption_model.config.use_flash_attention_2 = False
                if hasattr(self.caption_model.config, 'attn_implementation'):
                    self.caption_model.config.attn_implementation = 'eager'
            
            print(f"[DEBUG] Attention implementation: {getattr(self.caption_model.config, '_attn_implementation', 'eager')}")
            
        except Exception as e:
            if "flash" in str(e).lower() or "_supports_sdpa" in str(e):
                print(f"[WARN] Erreur flash_attn détectée, contournement...")
                
                # Patcher temporairement pour ignorer les attributs flash_attn
                import transformers
                original_getattr = transformers.modeling_utils.PreTrainedModel.__getattribute__
                
                def patched_getattr(self, name):
                    if name in ["_supports_sdpa", "_supports_flash_attn_2", "use_flash_attention_2"]:
                        return False
                    return original_getattr(self, name)
                
                transformers.modeling_utils.PreTrainedModel.__getattribute__ = patched_getattr
                
                try:
                    self.caption_model = AutoModelForCausalLM.from_pretrained(
                        str(model_path),
                        trust_remote_code=True,
                        torch_dtype=torch.float32,
                        attn_implementation='eager',
                    )
                finally:
                    # Restaurer
                    transformers.modeling_utils.PreTrainedModel.__getattribute__ = original_getattr
            else:
                raise
        
        self.caption_model = self.caption_model.to(self.device)
        
        print(f"[OK] icon_caption chargé (eager attention)")

    def detect_ui_elements(self, image: np.ndarray) -> List[Dict]:
        """
        Détecte tous les éléments UI avec captions sémantiques
        
        Args:
            image: Image numpy array (BGR)
            
        Returns:
            Liste de détections avec format:
            {
                'id': int,
                'label': str,           # Texte court (ex: "Search")
                'description': str,     # Caption complète (ex: "Search bar: Type to search")
                'bbox': [x, y, w, h],
                'center': (x, y),
                'confidence': float,
                'area': int,
                'type': 'ui_element'
            }
        """
        if self.icon_detect is None or self.caption_model is None:
            print("[OmniParser] ⚠️ OmniParser non initialisé")
            return []
        
        start_time = time.time()
        print(f"[OmniParser] 🔍 Démarrage détection... (image shape: {image.shape})")
        
        try:
            # 1. DÉTECTION avec YOLOv8
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            results = self.icon_detect.predict(
                image_rgb,
                conf=self.confidence_threshold,
                device=self.device,
                verbose=False
            )
            
            detect_time = time.time() - start_time
            print(f"[OmniParser] ⏱️ Temps détection: {detect_time:.2f}s")
            
            if len(results) == 0 or len(results[0].boxes) == 0:
                print("[OmniParser] ⚠️ Aucun élément détecté")
                return []
            
            # 2. EXTRACTION DES BBOXES
            boxes = results[0].boxes
            detections = []
            
            caption_start = time.time()
            
            for idx, box in enumerate(boxes):
                # Extraire bbox [x1, y1, x2, y2]
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].cpu().numpy()]
                
                # Convertir en [x, y, w, h]
                x, y, w, h = x1, y1, x2 - x1, y2 - y1
                
                # Confiance
                confidence = float(box.conf[0].cpu().numpy())
                
                # Centre
                center = (x + w // 2, y + h // 2)
                
                # Area
                area = w * h
                
                # 3. CAPTION SÉMANTIQUE avec Florence-2
                # Crop l'élément pour le caption
                crop = image_rgb[y:y+h, x:x+w]
                
                if crop.size == 0:
                    caption = f"Element {idx}"
                    label = f"elem_{idx}"
                else:
                    caption, label = self._generate_caption(crop)
                
                # Construction de la détection
                detection = {
                    'id': idx,
                    'label': label,
                    'description': caption,
                    'bbox': [x, y, w, h],
                    'center': center,
                    'confidence': confidence,
                    'area': area,
                    'type': 'ui_element',
                    'has_text': True  # OmniParser génère toujours une description
                }
                
                detections.append(detection)
                
                print(f"[OmniParser]   ✓ #{idx}: '{caption[:50]}...' @ ({center[0]},{center[1]}) conf={confidence:.2f}")
            
            caption_time = time.time() - caption_start
            total_time = time.time() - start_time
            
            print(f"[OmniParser] ⏱️ Temps caption: {caption_time:.2f}s")
            print(f"[OmniParser] ⏱️ Temps total: {total_time:.2f}s")
            print(f"[OmniParser] 📊 Résultats: {len(detections)} éléments UI avec captions\n")
            
            return detections
            
        except Exception as e:
            print(f"[WARN] Erreur détection OmniParser: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _generate_caption(self, crop_image: np.ndarray) -> Tuple[str, str]:
        """
        Génère une caption sémantique pour un élément UI avec Florence-2.
        Version Windows compatible (sans flash_attn).
        """
        try:
            # 1) Sanity checks sur le crop
            if crop_image is None or not isinstance(crop_image, np.ndarray):
                return "UI Element", "element"
            
            h, w = crop_image.shape[:2]
            if h <= 4 or w <= 4 or (h * w) < 16:
                return "UI Element (too small)", "element_small"

            # 2) Convert to PIL RGB
            from PIL import Image
            pil_image = Image.fromarray(crop_image).convert("RGB")

            # 3) Tâche Florence-2 prédéfinie
            task_prompt = "<CAPTION>"
            
            # 4) Préparation des inputs
            inputs = self.caption_processor(
                text=task_prompt,
                images=pil_image,
                return_tensors="pt"
            )

            # 5) Move tensors to device (float32 pour Windows)
            device = torch.device(self.device)
            
            for k, v in list(inputs.items()):
                if isinstance(v, torch.Tensor):
                    inputs[k] = v.to(device=device)

            # 6) Génération avec eager attention
            with torch.no_grad():
                generated_ids = self.caption_model.generate(
                    **inputs,
                    max_new_tokens=50,
                    num_beams=3,
                    do_sample=False
                )

            # 7) Décodage
            generated_text = self.caption_processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True
            )[0]

            # 8) Post-traitement
            caption = generated_text.replace(task_prompt, "").strip()
            
            if not caption or len(caption) < 3:
                caption = "UI Element"

            # Label court (5 premiers mots)
            label = ' '.join(caption.split()[:5])
            
            return caption, label

        except Exception as e:
            print(f"[WARN] Erreur caption: {e}")
            return "UI Element", "element"
    
    def detect_from_path(self, image_path: Path) -> List[Dict]:
        """Détecte éléments UI depuis un fichier image"""
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Impossible de charger: {image_path}")
        return self.detect_ui_elements(image)
    
    def format_for_llm(self, detections: List[Dict], max_items: int = 50) -> str:
        """
        Formate les détections pour le LLM avec descriptions ENRICHIES
        
        Format: ID X: Description sémantique | Position: (x, y) | Confiance: 0.XX
        """
        if not detections:
            return "Aucun élément cliquable détecté."
        
        lines = ["ÉLÉMENTS CLIQUABLES DÉTECTÉS:\n"]
        
        for det in detections[:max_items]:
            elem_id = det['id']
            description = det.get('description', det.get('label', 'Élément'))
            cx, cy = det['center']
            conf = det['confidence']
            
            # Format clair pour le LLM avec CAPTION SÉMANTIQUE
            line = f"  ID {elem_id}: {description}"
            line += f" | Position: ({cx}, {cy})"
            line += f" | Confiance: {conf:.2f}"
            
            lines.append(line)
        
        if len(detections) > max_items:
            lines.append(f"\n  ... et {len(detections) - max_items} autres éléments")
        
        return "\n".join(lines)


# Instance globale
omniparser = OmniParserDetector()