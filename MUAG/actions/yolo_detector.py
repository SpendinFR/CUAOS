"""
YOLOv11 Object Detector Module
Détection d'objets UI (boutons, icônes, éléments cliquables) avec YOLOv11
Complète PaddleOCR pour les éléments sans texte
"""
import cv2
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path

from config import (
    YOLO_MODEL,
    YOLO_CONFIDENCE,
    YOLO_IOU_THRESHOLD,
    YOLO_DEVICE
)


class YOLODetector:
    """
    Détection d'objets UI avec YOLOv11
    Détecte boutons, icônes, images cliquables
    """
    
    def __init__(self):
        """Initialise YOLOv11"""
        print("🔄 Initialisation YOLOv11...")
        
        try:
            from ultralytics import YOLO
            
            # Charger le modèle (télécharge automatiquement depuis Ultralytics)
            # Ne pas mettre de chemin, juste le nom du modèle
            self.model = YOLO('yolov11m')  # Auto-download depuis Ultralytics
            self.conf_threshold = YOLO_CONFIDENCE
            self.iou_threshold = YOLO_IOU_THRESHOLD
            self.device = YOLO_DEVICE
            
            print(f"✅ YOLOv11 chargé (yolov11m, device: {YOLO_DEVICE})")
            
        except Exception as e:
            print(f"❌ Erreur YOLOv11: {e}")
            print("   Vérifiez: pip install ultralytics")
            self.model = None
    
    def detect_objects(self, image: np.ndarray) -> List[Dict]:
        """
        Détecte les objets cliquables dans l'image
        
        Args:
            image: Image numpy array (BGR)
            
        Returns:
            Liste de détections:
            [{
                'label': 'button',
                'bbox': [x, y, width, height],
                'center': (x, y),
                'confidence': 0.89,
                'class_id': 12,
                'type': 'object'
            }, ...]
        """
        if self.model is None:
            return []
        
        try:
            # YOLOv11 inference
            results = self.model.predict(
                image,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                device=self.device,
                verbose=False
            )
            
            if not results or len(results) == 0:
                return []
            
            detections = []
            result = results[0]  # Premier (et seul) résultat
            
            # Extraire les boxes
            if result.boxes is not None:
                for box in result.boxes:
                    # Coordonnées xyxy
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # Convertir en xywh
                    x, y = int(x1), int(y1)
                    w, h = int(x2 - x1), int(y2 - y1)
                    
                    # Infos
                    conf = float(box.conf[0])
                    class_id = int(box.cls[0])
                    label = self.model.names[class_id]
                    
                    center = (x + w // 2, y + h // 2)
                    
                    detections.append({
                        'label': label,
                        'bbox': [x, y, w, h],
                        'center': center,
                        'confidence': conf,
                        'class_id': class_id,
                        'type': 'object'  # Pour fusion avec OCR
                    })
            
            return detections
            
        except Exception as e:
            print(f"⚠️ Erreur détection YOLO: {e}")
            return []
    
    def detect_from_path(self, image_path: Path) -> List[Dict]:
        """Détecte objets depuis un fichier image"""
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Impossible de charger: {image_path}")
        return self.detect_objects(image)
    
    def find_object(self, image: np.ndarray, label: str) -> Optional[Dict]:
        """
        Cherche un objet spécifique par son label
        
        Args:
            image: Image à analyser
            label: Label à chercher (ex: "button", "icon")
            
        Returns:
            Premier objet trouvé ou None
        """
        detections = self.detect_objects(image)
        
        for det in detections:
            if label.lower() in det['label'].lower():
                return det
        
        return None
    
    def filter_by_area(self, detections: List[Dict], min_area: int = 100, max_area: Optional[int] = None) -> List[Dict]:
        """
        Filtre les détections par taille
        Utile pour éliminer petits bruits ou grands fonds
        """
        filtered = []
        for det in detections:
            x, y, w, h = det['bbox']
            area = w * h
            
            if area < min_area:
                continue
            if max_area and area > max_area:
                continue
            
            filtered.append(det)
        
        return filtered
    
    def visualize_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Dessine les détections sur l'image (debug)
        """
        vis = image.copy()
        
        for det in detections:
            # Dessiner bbox
            x, y, w, h = det['bbox']
            cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 0, 255), 2)
            
            # Dessiner label
            label = det['label']
            conf = det['confidence']
            text = f"{label} ({conf:.2f})"
            cv2.putText(vis, text, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, (0, 0, 255), 1)
        
        return vis


# Instance globale
yolo_detector = YOLODetector()
