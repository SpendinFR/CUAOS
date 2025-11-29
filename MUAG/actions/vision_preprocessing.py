"""
Vision Preprocessing Module  
Ameliore la qualite des screenshots pour OCR et Object Detection
Utilise OpenCV pour debruitage, ajustement contraste, etc.
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from pathlib import Path

from config import (
    ENABLE_PREPROCESSING,
    PREPROCESSING_DENOISE,
    PREPROCESSING_CONTRAST, 
    PREPROCESSING_SHARPENING
)


class VisionPreprocessor:
    """
    Preprocessing dimages pour ameliorer OCR et Object Detection
    """
    
    def __init__(self):
        self.enabled = ENABLE_PREPROCESSING
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Pipeline complet preprocessing
        DOWNSCALE D'ABORD pour OCR/SAM2
        """
        # 1. DOWNSCALE AUTOMATIQUE (CRITIQUE pour 4K)
        # PaddleOCR et SAM2 marchent mal sur grandes images
        h, w = image.shape[:2]
        print(f"[DEBUG PREPROC] Image INPUT: {w}x{h} (shape: {image.shape})")
        
        # Si image > 1920 pixels de large, downscale a 1280x720
        MAX_WIDTH = 1280
        if w > MAX_WIDTH:
            scale = MAX_WIDTH / w
            new_w = MAX_WIDTH
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            print(f"[PREPROC] Downscaled: {w}x{h} -> {new_w}x{new_h}")
            print(f"[DEBUG PREPROC] Image AFTER RESIZE: {image.shape[1]}x{image.shape[0]} (shape: {image.shape})")
        else:
            print(f"[DEBUG PREPROC] NO RESIZE (image déjà <= {MAX_WIDTH}px)")
        
        # 2. Denoise (si active)
        if ENABLE_PREPROCESSING and PREPROCESSING_DENOISE:
            image = self.denoise_image(image)
        
        # 3. Contrast (si actif)
        if ENABLE_PREPROCESSING and PREPROCESSING_CONTRAST:
            image = self.adjust_contrast(image)
        
        # 4. Sharpening (optionnel)
        if ENABLE_PREPROCESSING and PREPROCESSING_SHARPENING:
            image = self.sharpen_image(image)
        
        print(f"[DEBUG PREPROC] Image OUTPUT FINAL: {image.shape[1]}x{image.shape[0]} (shape: {image.shape})")
        return image
    
    def denoise_image(self, image: np.ndarray) -> np.ndarray:
        """
        Debruitage avec fastNlMeansDenoisingColored
        Reduit le bruit tout en preservant les contours
        """
        return cv2.fastNlMeansDenoisingColored(
            image,
            None,
            h=3,  # Force du debruitage luminance
            hColor=3,  # Force du debruitage couleur
            templateWindowSize=7,
            searchWindowSize=21
        )
    
    def adjust_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Ajustement automatique du contraste avec CLAHE
        (Contrast Limited Adaptive Histogram Equalization)
        """
        # Convertir en LAB
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Appliquer CLAHE sur canal de lumiere
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Recombiner
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    def sharpen_image(self, image: np.ndarray) -> np.ndarray:
        """
        Sharpening avec filtre Laplacien
        """
        kernel = np.array([[0, -1, 0],
                          [-1, 5, -1],
                          [0, -1, 0]])
        return cv2.filter2D(image, -1, kernel)
    
    def extract_roi(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Extrait une Region of Interest (ROI)
        """
        x, y, w, h = bbox
        return image[y:y+h, x:x+w]
    
    def preprocess_from_path(self, image_path: Path) -> np.ndarray:
        """
        Charge et preprocess une image depuis un fichier
        """
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Impossible de charger l'image: {image_path}")
        return self.preprocess(image)


# Instance globale
preprocessor = VisionPreprocessor()
