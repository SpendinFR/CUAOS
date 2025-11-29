"""
Visual Annotator - Set-of-Mark (SoM) Implementation
Annote les screenshots avec des numéros pour chaque élément cliquable
Utilisé par Anthropic Claude Computer Use et GPT-4V Agent
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple


class VisualAnnotator:
    """Annotateur visuel pour le Set-of-Mark prompting"""
    
    def __init__(self):
        """Initialise l'annotateur avec les paramètres de style"""
        # Couleurs
        self.bbox_color = (128, 0, 128)    # Violet/Magenta pour le rectangle
        self.text_bg_color = (80, 0, 80)   # Violet foncé pour le fond étiquette
        self.text_color = (255, 255, 255)  # Blanc (garde)
        self.text_outline_color = (0, 0, 0)  # NOUVEAU : Noir pour contour
        self.bbox_thickness = 1
        self.text_thickness = 1
        
        # Police - plus grande pour meilleure visibilité
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.3  # Augmenté de 0.6 à 0.8
        
    def annotate_screenshot(
        self, 
        screenshot_path: Path, 
        clickable_elements: List[Dict],
        output_path: Path = None
    ) -> Path:
        """
        Annote un screenshot avec les IDs des éléments cliquables
        
        Args:
            screenshot_path: Chemin vers le screenshot original
            clickable_elements: Liste des éléments détectés par fusion OCR+SAM
            output_path: Chemin de sortie (optionnel)
            
        Returns:
            Path vers l'image annotée
        """
        # Charger l'image
        img = cv2.imread(str(screenshot_path))
        if img is None:
            raise ValueError(f"Impossible de charger l'image: {screenshot_path}")
        
        # Créer une copie pour l'annotation
        annotated = img.copy()
        
        # Fonction helper pour détecter collision entre rectangles
        def rectangles_overlap(rect1, rect2, tolerance=2):
            """Vérifie si 2 rectangles se chevauchent (avec tolérance)"""
            x1, y1, w1, h1 = rect1
            x2, y2, w2, h2 = rect2
            
            # Ajouter tolérance (permet petit chevauchement acceptable)
            if (x1 + w1 < x2 - tolerance or
                x2 + w2 < x1 - tolerance or
                y1 + h1 < y2 - tolerance or
                y2 + h2 < y1 - tolerance):
                return False
            return True
        
        # Extraire toutes les bboxes pour vérification collision
        all_bboxes = [elem.get('bbox', [0, 0, 0, 0]) for elem in clickable_elements]
        
        # Annoter chaque élément
        for idx, elem in enumerate(clickable_elements):
            # Extraire les informations
            bbox = elem.get('bbox', [0, 0, 0, 0])  # [x, y, w, h]
            center = elem.get('center', (0, 0))
            
            # Palette de couleurs rotatives pour distinguer éléments voisins
            color_palette = [
                ((150, 30, 150), (100, 20, 100)),   # 1. Violet/Magenta foncé
                ((0, 70, 150), (0, 50, 120)),       # 2. Orange très foncé
                ((150, 70, 30), (120, 50, 20)),     # 3. Bleu/Cyan très foncé
                ((30, 100, 30), (20, 80, 20)),      # 4. Vert très foncé
                ((70, 30, 150), (50, 20, 120)),     # 5. Rouge-violet foncé
                ((100, 100, 0), (80, 80, 0)),       # 6. Cyan foncé
                ((0, 100, 100), (0, 80, 80)),       # 7. Jaune/Or foncé
                ((100, 0, 100), (80, 0, 80)),       # 8. Magenta foncé
                ((50, 100, 150), (40, 80, 120)),    # 9. Orange-brun foncé
                ((150, 50, 100), (120, 40, 80)),    # 10. Rose-violet foncé
            ]
            bbox_color, _ = color_palette[idx % len(color_palette)]
            text_bg_color = bbox_color  # Même couleur pour box et étiquette            
            
            # Dessiner la bounding box
            x, y, w, h = bbox
            cv2.rectangle(
                annotated, 
                (x, y), 
                (x + w, y + h),
                bbox_color, 
                self.bbox_thickness
            )
            
            # Préparer le texte de l'ID
            id_text = str(idx)
            
            # Calculer la taille du texte
            (text_w, text_h), baseline = cv2.getTextSize(
                id_text, 
                self.font, 
                self.font_scale, 
                self.text_thickness
            )
            
            # Positionnement intelligent pour éviter collisions
            text_x = x + (w - text_w) // 2  # Centré par défaut
            
            # Essayer plusieurs positions dans l'ordre de priorité
            positions = [
                ('top', x + (w - text_w) // 2, y - 5 - text_h),              # Au-dessus
                ('bottom', x + (w - text_w) // 2, y + h + 2),                 # En dessous
                ('left', x - text_w - 2, y + (h - text_h) // 2),              # À gauche
                ('right', x + w + 2, y + (h - text_h) // 2),                  # À droite
            ]
            
            # Tester chaque position
            best_pos = positions[0]  # Par défaut : au-dessus
            for pos_name, px, py in positions:
                # Rectangle de l'étiquette à cette position
                label_rect = [px, py, text_w, text_h + 5]
                
                # Vérifier collision avec toutes les autres bboxes
                has_collision = False
                for j, other_bbox in enumerate(all_bboxes):
                    if j != idx and rectangles_overlap(label_rect, other_bbox):
                        has_collision = True
                        break
                
                # Si pas de collision, utiliser cette position
                if not has_collision:
                    text_x, text_y = px, py + text_h  # Ajuster pour baseline
                    break
            else:
                # Si toutes les positions ont collision, garder au-dessus
                text_x = x + (w - text_w) // 2
                text_y = y - 5
            
            # S'assurer que le texte ne dépasse pas
            text_x = max(2, min(text_x, img.shape[1] - text_w - 2))
            text_y = max(text_h + 2, min(text_y, img.shape[0] - 2))
            
            # Bordure blanche autour de l'étiquette
            padding = 2
            white_padding = padding + 1
            
            # Dessiner bordure blanche
            cv2.rectangle(
                annotated,
                (text_x - white_padding, text_y - text_h - white_padding),
                (text_x + text_w + white_padding, text_y + baseline + white_padding),
                (255, 255, 255),  # Blanc
                -1
            )
            
            # Dessiner le fond coloré
            cv2.rectangle(
                annotated,
                (text_x - padding, text_y - text_h - padding),
                (text_x + text_w + padding, text_y + baseline + padding),
                text_bg_color,  # Couleur de la palette
                -1
            )
            
            # Dessiner l'ID
            cv2.putText(
            annotated,
            id_text,
            (text_x, text_y),
            self.font,
            self.font_scale,
            (0, 0, 0),  # Noir
            3,  # Plus épais pour le contour
            cv2.LINE_AA
            )

            # Texte blanc par-dessus
            cv2.putText(
                annotated,
                id_text,
                (text_x, text_y),
                self.font,
                self.font_scale,
                self.text_color,  # Blanc
                self.text_thickness,
                cv2.LINE_AA
            )
        
        
        # Sauvegarder l'image annotée
        if output_path is None:
            output_path = screenshot_path.parent / f"annotated_{screenshot_path.name}"
        
        cv2.imwrite(str(output_path), annotated)
        print(f"📝 Image annotée avec {len(clickable_elements)} éléments: {output_path}")
        
        return output_path
    
    def annotate_with_highlights(
        self,
        screenshot_path: Path,
        clickable_elements: List[Dict],
        highlight_ids: List[int] = None,
        output_path: Path = None
    ) -> Path:
        """
        Version avancée avec mise en évidence de certains éléments
        
        Args:
            screenshot_path: Chemin vers le screenshot
            clickable_elements: Liste des éléments
            highlight_ids: IDs à mettre en évidence (optionnel)
            output_path: Chemin de sortie
            
        Returns:
            Path vers l'image annotée
        """
        # Charger l'image
        img = cv2.imread(str(screenshot_path))
        if img is None:
            raise ValueError(f"Impossible de charger l'image: {screenshot_path}")
        
        annotated = img.copy()
        highlight_ids = highlight_ids or []
        
        # Annoter chaque élément
        for idx, elem in enumerate(clickable_elements):
            bbox = elem.get('bbox', [0, 0, 0, 0])
            center = elem.get('center', (0, 0))
            
            # Couleur différente pour les éléments mis en évidence
            is_highlighted = idx in highlight_ids
            bbox_color = (0, 0, 255) if is_highlighted else self.bbox_color  # Rouge si highlight
            text_bg_color = (0, 0, 200) if is_highlighted else self.text_bg_color
            thickness = 3 if is_highlighted else self.bbox_thickness
            
            # Dessiner la bounding box
            x, y, w, h = bbox
            cv2.rectangle(
                annotated, 
                (x, y), 
                (x + w, y + h),
                bbox_color, 
                thickness
            )
            
            # Texte de l'ID
            id_text = str(idx)
            (text_w, text_h), baseline = cv2.getTextSize(
                id_text, 
                self.font, 
                self.font_scale, 
                self.text_thickness
            )
            
            text_x = x
            text_y = y - 5 if y > 30 else y + h + text_h + 5
            padding = 4
            
            # Fond du texte
            cv2.rectangle(
                annotated,
                (text_x - padding, text_y - text_h - padding),
                (text_x + text_w + padding, text_y + baseline + padding),
                text_bg_color,
                -1
            )
            
            # Texte
            cv2.putText(
                annotated,
                id_text,
                (text_x, text_y),
                self.font,
                self.font_scale,
                self.text_color,
                self.text_thickness,
                cv2.LINE_AA
            )
        
        # Sauvegarder
        if output_path is None:
            output_path = screenshot_path.parent / f"annotated_highlighted_{screenshot_path.name}"
        
        cv2.imwrite(str(output_path), annotated)
        return output_path


# Instance globale
annotator = VisualAnnotator()