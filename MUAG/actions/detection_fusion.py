"""
Detection Fusion Module
Fusionne les détections PaddleOCR + SAM/OmniParser en une liste unifiée
Enrichit SAM avec texte OCR pour descriptions claires
Élimine les doublons avec NMS (Non-Maximum Suppression)
"""
import numpy as np
from typing import List, Dict, Tuple, Optional

from config import FUSION_NMS_THRESHOLD


class DetectionFusion:
    """
    Fusionne OCR et SAM/OmniParser Detection
    Crée une liste complète d'éléments cliquables avec descriptions claires
    """

    def __init__(self):
        self.nms_threshold = FUSION_NMS_THRESHOLD

    def fuse(self, ocr_detections: List[Dict], sam_detections: List[Dict]) -> List[Dict]:
        """
        Fusionne OCR + SAM/OmniParser intelligemment

        Pipeline:
        1. Enrichir SAM avec texte OCR (si texte dans zone SAM)
        2. Combiner OCR seul + SAM enrichi
        3. NMS pour éliminer doublons
        4. Trier par confiance

        Args:
            ocr_detections: Détections PaddleOCR
            sam_detections: Détections SAM/OmniParser

        Returns:
            Liste fusionnée, avec descriptions claires
        """
        print("\n[FUSION] Démarrage fusion...")
        print(f"[FUSION]   OCR: {len(ocr_detections)} textes")
        print(f"[FUSION]   SAM: {len(sam_detections)} éléments UI")

        # 1. ENRICHIR SAM avec texte OCR
        enriched_sam = self._enrich_sam_with_ocr(sam_detections, ocr_detections)
        print(f"[FUSION]   SAM enrichi: {len(enriched_sam)} éléments")

        # 2. SÉPARER OCR non-utilisé et SAM enrichi
        used_ocr_ids = set()
        for sam in enriched_sam:
            if "ocr_ids" in sam:
                used_ocr_ids.update(sam["ocr_ids"])

        standalone_ocr_raw = [
            ocr for i, ocr in enumerate(ocr_detections) if i not in used_ocr_ids
        ]

        standalone_ocr: List[Dict] = []
        for ocr in standalone_ocr_raw:
            enriched_ocr = ocr.copy()
            text = ocr.get("text", "texte")
            enriched_ocr["label"] = text
            enriched_ocr["description"] = text
            enriched_ocr["type"] = "text"
            enriched_ocr["has_text"] = True
            standalone_ocr.append(enriched_ocr)

        print(f"[FUSION]   OCR standalone: {len(standalone_ocr)} textes")

        # 3. COMBINER
        all_detections = standalone_ocr + enriched_sam

        if not all_detections:
            print("[FUSION] Attention: aucune détection après fusion")
            return []

        # 4. NMS pour éliminer doublons
        fused = self.apply_nms(all_detections)
        print(f"[FUSION]   Après NMS: {len(fused)} éléments")

        # 5. TRIER par confiance décroissante
        fused.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)

        # 6. AJOUTER ID unique
        for i, det in enumerate(fused):
            det["id"] = i
            det["unique_id"] = f"elem_{i}"

        print(f"[FUSION] Fin fusion: {len(fused)} éléments cliquables\n")

        return fused

    def _enrich_sam_with_ocr(
        self, sam_detections: List[Dict], ocr_detections: List[Dict]
    ) -> List[Dict]:
        """
        Enrichit chaque élément SAM/OmniParser avec le texte OCR qu'il contient
        """
        enriched: List[Dict] = []

        for sam_idx, sam in enumerate(sam_detections):
            sx, sy, sw, sh = sam.get("bbox", [0, 0, 0, 0])
            sam_area = sw * sh

            contained_ocr = []
            ocr_ids = []

            for ocr_idx, ocr in enumerate(ocr_detections):
                ox, oy = ocr.get("center", (0, 0))

                if sx <= ox <= sx + sw and sy <= oy <= sy + sh:
                    contained_ocr.append(ocr.get("text", ""))
                    ocr_ids.append(ocr_idx)

            original_label = sam.get("label")
            original_desc = sam.get("description")

            if contained_ocr:
                combined_text = " ".join(t for t in contained_ocr if t)

                if sw < sh * 2 and sam_area < 10000:
                    elem_type = "Bouton"
                elif sw > sh * 3:
                    elem_type = "Barre"
                elif sam_area > 50000:
                    elem_type = "Panneau"
                else:
                    elem_type = "Élément"

                description = original_desc or f"{elem_type}: {combined_text}"
                label = original_label or combined_text
                has_text = True
            else:
                aspect_ratio = sw / sh if sh > 0 else 1.0

                if aspect_ratio > 3:
                    elem_type = "Barre horizontale"
                elif aspect_ratio < 0.33:
                    elem_type = "Barre verticale"
                elif 0.8 < aspect_ratio < 1.2 and sam_area < 5000:
                    elem_type = "Icône"
                elif sam_area < 2000:
                    elem_type = "Petit bouton"
                elif sam_area < 10000:
                    elem_type = "Bouton"
                elif sam_area < 50000:
                    elem_type = "Zone UI"
                else:
                    elem_type = "Grand panneau"

                description = original_desc or f"{elem_type} {sw}x{sh}px"
                label = original_label or f"{elem_type.lower()}_{sam_idx}"
                has_text = False

            enriched_sam = {
                "label": label,
                "description": description,
                "bbox": sam.get("bbox", [0, 0, 0, 0]),
                "center": sam.get("center", (0, 0)),
                "confidence": sam.get("confidence", 0.0),
                "area": sam.get("area", sam_area),
                "type": "ui_element",
                "has_text": has_text,
                "ocr_ids": ocr_ids,
                "sam_index": sam_idx,
            }

            if "mask" in sam:
                enriched_sam["mask"] = sam["mask"]

            enriched.append(enriched_sam)

            cx, cy = enriched_sam["center"]
            status = "avec texte" if has_text else "sans texte"
            print(
                f"[FUSION]     SAM #{sam_idx}: '{description}' @ ({cx},{cy}) - {status}"
            )

        return enriched

    def apply_nms(self, detections: List[Dict]) -> List[Dict]:
        """
        Non-Maximum Suppression pour éliminer doublons
        """
        if len(detections) <= 1:
            return detections

        sorted_dets = sorted(
            detections, key=lambda x: x.get("confidence", 0.0), reverse=True
        )

        kept: List[Dict] = []

        for det in sorted_dets:
            overlap = False
            for kept_det in kept:
                iou = self.calculate_iou(det["bbox"], kept_det["bbox"])
                if iou > self.nms_threshold:
                    overlap = True
                    break

            if not overlap:
                kept.append(det)

        return kept

    def calculate_iou(self, bbox1: List[int], bbox2: List[int]) -> float:
        """
        Calcule Intersection over Union (IoU) entre deux bboxes
        """
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2

        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection = (x_right - x_left) * (y_bottom - y_top)

        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection

        if union == 0:
            return 0.0

        return float(intersection) / float(union)

    def find_clickable_by_text(
        self, detections: List[Dict], search_text: str
    ) -> List[Dict]:
        """
        Trouve tous les éléments contenant un texte
        """
        matched: List[Dict] = []
        search = search_text.lower()

        for det in detections:
            if search in det.get("label", "").lower():
                matched.append(det)
            elif search in det.get("description", "").lower():
                matched.append(det)

        return matched

    def get_clickables_in_area(
        self, detections: List[Dict], area: Tuple[int, int, int, int]
    ) -> List[Dict]:
        """
        Retourne les éléments cliquables dans une zone
        """
        ax, ay, aw, ah = area
        in_area: List[Dict] = []

        for det in detections:
            cx, cy = det.get("center", (0, 0))
            if ax <= cx <= ax + aw and ay <= cy <= ay + ah:
                in_area.append(det)

        return in_area

    def format_for_llm(self, detections: List[Dict], max_items: int = 50) -> str:
        """
        Formate les détections pour le LLM avec descriptions claires
        """
        if not detections:
            return "Aucun élément cliquable détecté."

        lines = ["ÉLÉMENTS CLIQUABLES DÉTECTÉS:\n"]

        for det in detections[:max_items]:
            elem_id = det.get("id")
            description = det.get("description", det.get("label", "Élément"))
            cx, cy = det.get("center", (0, 0))
            conf = det.get("confidence", 0.0)

            line = f"  ID {elem_id}: {description}"
            line += f" | Position: ({cx}, {cy})"
            line += f" | Confiance: {conf:.2f}"

            lines.append(line)

        if len(detections) > max_items:
            lines.append(f"\n  ... et {len(detections) - max_items} autres éléments")

        return "\n".join(lines)

    def get_element_by_id(
        self, detections: List[Dict], element_id: int
    ) -> Optional[Dict]:
        """
        Récupère un élément par son ID
        """
        for det in detections:
            if det.get("id") == element_id:
                return det
        return None


# Instance globale
fusion = DetectionFusion()
