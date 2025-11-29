"""
Screen Monitoring Module
Détecte les changements visuels entre frames :
- Popups
- Changements d'état (boutons qui changent de couleur)
- Nouvelles fenêtres
Utile pour savoir si une action a eu un effet
"""
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import deque

from config import (
    ENABLE_SCREEN_MONITORING,
    MONITOR_DIFF_THRESHOLD,
    MONITOR_HISTORY_SIZE
)


class ScreenMonitor:
    """
    Moniteur de changements d'écran
    Compare frames successives pour détecter changements visuels
    """
    
    def __init__(self):
        self.enabled = ENABLE_SCREEN_MONITORING
        self.diff_threshold = MONITOR_DIFF_THRESHOLD
        
        # Historique des frames précédentes
        self.history = deque(maxlen=MONITOR_HISTORY_SIZE)
        
        # Stats de changements
        self.last_change_percent = 0.0
        self.significant_changes = []
    
    def add_frame(self, frame: np.ndarray) -> Dict:
        """
        Ajoute une nouvelle frame et détecte changements
        
        Args:
            frame: Image courante (BGR)
            
        Returns:
            Rapport de changements: {
                'changed': bool,
                'change_percent': float,
                'change_type': str,  # 'popup', 'state_change', 'new_window', 'minor'
                'change_areas': List[bbox]  # Zones qui ont changé
            }
        """
        if not self.enabled:
            return self._empty_report()
        
        # Première frame
        if len(self.history) == 0:
            self.history.append(frame.copy())
            return self._empty_report()
        
        # Comparer avec frame précédente
        prev_frame = self.history[-1]
        report = self.detect_changes(prev_frame, frame)
        
        # Ajouter à l'historique
        self.history.append(frame.copy())
        
        # Sauvegarder stats
        self.last_change_percent = report['change_percent']
        
        if report['changed']:
            self.significant_changes.append({
                'timestamp': len(self.history),
                'type': report['change_type'],
                'percent': report['change_percent']
            })
        
        return report
    
    def detect_changes(self, frame1: np.ndarray, frame2: np.ndarray) -> Dict:
        """
        Détecte les changements entre deux frames
        """
        # Convertir en niveaux de gris
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Différence absolue
        diff = cv2.absdiff(gray1, gray2)
        
        # Seuil binaire
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        # Calculer pourcentage de changement
        total_pixels = diff.shape[0] * diff.shape[1]
        changed_pixels = np.count_nonzero(thresh)
        change_percent = changed_pixels / total_pixels
        
        # Déterminer si changement significatif
        changed = change_percent > self.diff_threshold
        
        # Analyser le type de changement
        change_type = self._classify_change(thresh, change_percent) if changed else 'none'
        
        # Trouver les zones qui ont changé
        change_areas = self._find_change_areas(thresh) if changed else []
        
        return {
            'changed': changed,
            'change_percent': float(change_percent),
            'change_type': change_type,
            'change_areas': change_areas
        }
    
    def _classify_change(self, diff_thresh: np.ndarray, percent: float) -> str:
        """
        Classifie le type de changement
        
        Returns:
            'popup', 'state_change', 'new_window', ou 'minor'
        """
        # Popup: changement concentré au centre
        if self._is_popup(diff_thresh):
            return 'popup'
        
        # New window: changement sur toute la fenêtre
        if percent > 0.3:  # Plus de 30% de changement
            return 'new_window'
        
        # State change: changement localisé (bouton, etc.)
        if percent < 0.15:  # Moins de 15%
            return 'state_change'
        
        return 'minor'
    
    def _is_popup(self, diff_thresh: np.ndarray) -> bool:
        """
        Détecte si le changement ressemble à un popup
        (changement rectangulaire au centre de l'écran)
        """
        h, w = diff_thresh.shape
        center_y, center_x = h // 2, w // 2
        
        # Zone centrale (50% de l'écran)
        y1, y2 = center_y - h // 4, center_y + h // 4
        x1, x2 = center_x - w // 4, center_x + w // 4
        
        center_region = diff_thresh[y1:y2, x1:x2]
        
        # Si beaucoup de changements au centre
        center_changed = np.count_nonzero(center_region) / center_region.size
        
        return center_changed > 0.2  # 20% de la zone centrale a changé
    
    def _find_change_areas(self, diff_thresh: np.ndarray) -> List[List[int]]:
        """
        Trouve les bounding boxes des zones qui ont changé
        
        Returns:
            Liste de [x, y, width, height]
        """
        # Trouver contours
        contours, _ = cv2.findContours(diff_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        areas = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filtrer les petits changements (bruit)
            if w * h > 500:  # Au moins 500 pixels
                areas.append([x, y, w, h])
        
        return areas
    
    def get_change_summary(self) -> str:
        """
        Résumé des changements récents pour le LLM
        """
        if self.last_change_percent < self.diff_threshold:
            return "Pas de changement visuel détecté."
        
        summary = f"Changement détecté: {self.last_change_percent*100:.1f}% de l'écran a changé.\n"
        
        if self.significant_changes:
            recent = self.significant_changes[-3:]  # 3 derniers
            summary += "Changements récents:\n"
            for change in recent:
                summary += f"  - {change['type']} ({change['percent']*100:.1f}%)\n"
        
        return summary
    
    def reset_history(self):
        """Réinitialise l'historique"""
        self.history.clear()
        self.significant_changes.clear()
        self.last_change_percent = 0.0
    
    def _empty_report(self) -> Dict:
        """Rapport vide (pas de changement)"""
        return {
            'changed': False,
            'change_percent': 0.0,
            'change_type': 'none',
            'change_areas': []
        }
    
    def visualize_changes(self, frame1: np.ndarray, frame2: np.ndarray) -> np.ndarray:
        """
        Visualise les changements entre deux frames (debug)
        
        Returns:
            Image avec zones de changement en rouge
        """
        report = self.detect_changes(frame1, frame2)
        
        vis = frame2.copy()
        
        # Dessiner les zones de changement
        for bbox in report['change_areas']:
            x, y, w, h = bbox
            cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 0, 255), 2)
        
        # Ajouter texte info
        info = f"{report['change_type']} - {report['change_percent']*100:.1f}%"
        cv2.putText(vis, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   1, (0, 0, 255), 2)
        
        return vis


# Instance globale
screen_monitor = ScreenMonitor()
