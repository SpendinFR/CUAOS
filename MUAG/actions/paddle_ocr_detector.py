"""
PaddleOCR Detector Module
Detection de texte avec coordonnees precises en utilisant PaddleOCR
"""
import cv2
import numpy as np
import time
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from config import (
    PADDLE_OCR_LANG,
    PADDLE_OCR_USE_GPU,
    PADDLE_OCR_CONFIDENCE_THRESHOLD
)


class PaddleOCRDetector:
    """
    Detection OCR avec PaddleOCR
    Retourne texte + bounding boxes precises
    """
    
    def __init__(self):
        """Initialise PaddleOCR"""
        print("[OCR] Initialisation PaddleOCR...")
        
        try:
            from paddleocr import PaddleOCR
            import inspect
            import os
            
            # Langue principale
            lang = PADDLE_OCR_LANG if isinstance(PADDLE_OCR_LANG, str) else PADDLE_OCR_LANG[0]
            
            # Désactiver les logs PaddlePaddle pour améliorer la vitesse
            os.environ['FLAGS_logtostderr'] = '0'
            os.environ['FLAGS_minloglevel'] = '3'
            
            # On lit la signature de __init__ pour ne passer que les kwargs supportés
            init_sig = inspect.signature(PaddleOCR.__init__)
            supported_params = init_sig.parameters.keys()
            
            # L'image préprocessed est max 1280px de large (VisionPreprocessor)
            DET_LIMIT_SIDE_LEN = 1280
            
            # On prépare tous les kwargs souhaités
            candidate_kwargs = {
                "lang": lang,
                "use_angle_cls": True,
                # Utiliser le GPU si la version le supporte et si config l'indique
                "use_gpu": bool(PADDLE_OCR_USE_GPU),
                # Limites de taille pour éviter les resizes internes inutiles
                "det_limit_side_len": DET_LIMIT_SIDE_LEN,
                "det_limit_type": "max",
                # Pour les versions récentes (3.x) qui ont un doc_preprocessor
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "use_textline_orientation": False,
            }
            
            # On ne garde que les paramètres effectivement supportés par cette version
            ocr_kwargs = {
                name: value
                for name, value in candidate_kwargs.items()
                if name in supported_params
            }
            
            self.ocr = PaddleOCR(**ocr_kwargs)
            self.conf_threshold = PADDLE_OCR_CONFIDENCE_THRESHOLD
            
            # Log des options réellement utilisées (utile pour debug)
            used_opts = ", ".join(f"{k}={v}" for k, v in ocr_kwargs.items() if k != "lang")
            print(
                f"[OK] PaddleOCR chargé (langues: {PADDLE_OCR_LANG}, "
                f"seuil: {self.conf_threshold}, options: {{{used_opts}}})"
            )
            
        except Exception as e:
            print(f"[ERROR] ERREUR initialisation PaddleOCR: {e}")
            import traceback
            traceback.print_exc()
            self.ocr = None
    
    def detect_text(self, image: np.ndarray) -> List[Dict]:
        """
        Detecte tout le texte dans l'image avec PaddleOCR
        """
        if self.ocr is None:
            print("[OCR] ATTENTION: OCR non initialise")
            return []
        
        start_time = time.time()
        print(f"[OCR] Demarrage detection... (image shape: {image.shape})")
        
        try:
            result = self.ocr.ocr(image)
            ocr_time = time.time() - start_time
            print(f"[OCR] Temps detection: {ocr_time:.2f}s")
            
            if not result or len(result) == 0:
                print("[OCR] ATTENTION: PaddleOCR n'a retourne aucun resultat")
                return []
            
            # Nouveau format PaddleOCR: result[0] est un OCRResult object
            ocr_result = result[0]
            
            # Extraire les lignes détectées depuis l'objet OCRResult
            lines = []

            # Format PaddleX OCRResult (c'est un dict-like object)
            if isinstance(ocr_result, dict) or hasattr(ocr_result, 'keys'):
                print(f"[OCR] Format PaddleX OCRResult (dict-like)")
                print(f"[OCR] Clés disponibles: {list(ocr_result.keys())}")
                
                # Essayer d'accéder aux données OCR
                # PaddleX stocke souvent les résultats dans des clés comme 'dt_polys', 'rec_texts', 'rec_scores'
                # ou directement itérable
                
                # Cas 1: Itérer directement sur l'objet
                try:
                    for item in ocr_result:
                        if isinstance(item, dict):
                            # Chaque item est un dict avec les infos
                            lines.append(item)
                        elif isinstance(item, (list, tuple)) and len(item) >= 2:
                            # Format [bbox, (text, score)]
                            lines.append(item)
                    print(f"[OCR] Extraction par iteration: {len(lines)} lignes")
                except:
                    pass
                
                # Cas 2: Accéder via des clés spécifiques
                if len(lines) == 0:
                    if 'dt_polys' in ocr_result and 'rec_texts' in ocr_result and 'rec_scores' in ocr_result:
                        dt_polys = ocr_result['dt_polys']
                        rec_texts = ocr_result['rec_texts']
                        rec_scores = ocr_result['rec_scores']
                        
                        if dt_polys and rec_texts and rec_scores:
                            for poly, text, score in zip(dt_polys, rec_texts, rec_scores):
                                lines.append([poly, (text, score)])
                        print(f"[OCR] Extraction via clés dt_polys: {len(lines)} lignes")
                    
                    elif 'boxes' in ocr_result and 'texts' in ocr_result and 'scores' in ocr_result:
                        boxes = ocr_result['boxes']
                        texts = ocr_result['texts']
                        scores = ocr_result['scores']
                        
                        if boxes and texts and scores:
                            for box, text, score in zip(boxes, texts, scores):
                                lines.append([box, (text, score)])
                        print(f"[OCR] Extraction via clés boxes: {len(lines)} lignes")

            elif hasattr(ocr_result, 'dt_polys') and hasattr(ocr_result, 'rec_text') and hasattr(ocr_result, 'rec_score'):
                # Format OCRResult avec attributs dt_polys (ancien PaddleOCR)
                dt_polys = ocr_result.dt_polys
                rec_texts = ocr_result.rec_text
                rec_scores = ocr_result.rec_score
                
                if dt_polys is not None and rec_texts is not None and rec_scores is not None:
                    for poly, text, score in zip(dt_polys, rec_texts, rec_scores):
                        lines.append([poly, (text, score)])
                        
                print(f"[OCR] Format OCRResult avec attributs: {len(lines)} lignes")

            elif isinstance(ocr_result, list):
                # Ancien format: liste simple
                lines = ocr_result
                print(f"[OCR] Format liste detecte: {len(lines)} lignes")

            else:
                print(f"[OCR] ATTENTION: Format inconnu (type: {type(ocr_result)})")
                print(f"[OCR] Attributs disponibles: {dir(ocr_result)}")
                return []
            
            if not lines or lines is None or len(lines) == 0:
                print(f"[OCR] ATTENTION: Aucune ligne detectee")
                return []
            
            detections = []
            total_lines = len(lines)
            filtered_count = 0
            low_conf_count = 0
            
            for line in lines:
                try:
                    # Gérer différents formats de line
                    if isinstance(line, dict):
                        # Format dict direct
                        bbox_poly = line.get('bbox') or line.get('box') or line.get('dt_poly')
                        text = line.get('text') or line.get('rec_text')
                        confidence = line.get('score') or line.get('rec_score') or line.get('confidence')
                    elif isinstance(line, (list, tuple)) and len(line) >= 2:
                        # Format [bbox, (text, score)]
                        bbox_poly = line[0]
                        text_info = line[1]
                        
                        if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                            text = text_info[0]
                            confidence = text_info[1]
                        else:
                            continue
                    else:
                        continue
                    
                    # Validation
                    text = str(text).strip() if text else ""
                    confidence = float(confidence) if confidence else 0.0
                    
                    if not text:
                        continue
                    
                    if confidence < self.conf_threshold:
                        low_conf_count += 1
                        continue
                    
                    bbox_rect = self._polygon_to_bbox(bbox_poly)
                    center = self._bbox_center(bbox_rect)
                    
                    detections.append({
                        'text': text,
                        'bbox': bbox_rect,
                        'center': center,
                        'confidence': float(confidence),
                        'polygon': bbox_poly,
                        'type': 'text'
                    })
                    print(f"[OCR]   OK '{text}' @ ({center[0]},{center[1]}) conf={confidence:.2f}")
                except Exception as e:
                    filtered_count += 1
                    print(f"[OCR]   Erreur parsing ligne: {e}")
                    continue
            
            print(f"[OCR] RESULTATS: {len(detections)} textes detectes sur {total_lines} lignes")
            if low_conf_count > 0:
                print(f"[OCR]    (ignore {low_conf_count} textes avec confiance < {self.conf_threshold})")
            if filtered_count > 0:
                print(f"[OCR]    (ignore {filtered_count} lignes avec erreurs de parsing)")
            
            return detections
            
        except Exception as e:
            print(f"[WARN] Erreur detection OCR: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def detect_from_path(self, image_path: Path) -> List[Dict]:
        """Detecte texte depuis un fichier image"""
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Impossible de charger: {image_path}")
        return self.detect_text(image)
    
    def _polygon_to_bbox(self, polygon: List[List[float]]) -> List[int]:
        """Convertit un polygon en bounding box rectangulaire"""
        # Gérer différents formats de polygon
        if isinstance(polygon, np.ndarray):
            polygon = polygon.tolist()
        
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        
        return [
            int(x_min),
            int(y_min),
            int(x_max - x_min),
            int(y_max - y_min)
        ]
    
    def _bbox_center(self, bbox: List[int]) -> Tuple[int, int]:
        """Calcule le centre d'une bbox"""
        x, y, w, h = bbox
        return (x + w // 2, y + h // 2)


# Instance globale
paddle_ocr = PaddleOCRDetector()