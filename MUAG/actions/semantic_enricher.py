"""
Semantic Enricher Module
Fusionne OCR + OmniParser pour enrichir les descriptions UI
Approche : OCR proche + patterns visuels essentiels + contexte spatial
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
import re


class SemanticEnricher:
    """
    Enrichit les détections OmniParser avec :
    1. Texte OCR à proximité
    2. Patterns visuels courants (classification simple)
    3. Contexte spatial (position + type de contexte)
    """

    # Patterns visuels essentiels (clés = bouts de captions OmniParser)
    VISUAL_PATTERNS = {
        # Navigation / flèches
        "arrow pointing left": ["back"],
        "left arrow": ["back", "previous"],
        "back arrow": ["back", "previous"],
        "arrow pointing right": ["forward"],
        "right arrow": ["forward", "next"],
        "forward arrow": ["forward", "next"],
        "arrow": ["navigation", "direction"],

        # Actions / croix / fermeture
        "x icon": ["close"],
        "x button": ["close"],
        "black cross": ["close"],
        "white cross": ["close"],
        "cross": ["close", "exit", "dismiss"],

        # Search
        "magnifying glass": ["search_or_zoom"],
        "search icon": ["search_or_zoom"],
        "loupe": ["search_or_zoom"],
        "search bar": ["search"],
        "search field": ["search"],

        # Actions génériques
        "star": ["favorite", "bookmark"],
        "plus": ["add", "new", "create"],
        "minus": ["remove", "delete", "minimize"],
        "gear": ["settings"],
        "cog": ["settings"],

        # Menus
        "three dots": ["menu", "more"],
        "hamburger": ["menu", "navigation"],
        "three lines": ["menu", "navigation"],

        # Logos
        "google": ["logo", "branding"],
        "facebook": ["logo", "link"],
        "github": ["logo", "link"],
        "logo": ["branding", "visual"],
    }

    # Contextes spatiaux lisibles pour un navigateur
    SPATIAL_CONTEXTS_BROWSER = {
        "top-left": "browser navigation",
        "top-right": "browser controls",
        "top-center": "browser toolbar",
        "center": "main content",
        "bottom": "taskbar or footer",
    }

    def __init__(self):
        print("[SemanticEnricher] Initialisation...")

    def enrich(
        self,
        clickable_elements: List[Dict],
        ocr_results: List[Dict],
        image_shape: Tuple[int, int] = None,
        context: str = "browser",
    ) -> List[Dict]:
        """
        Enrichit les éléments cliquables avec OCR + patterns + contexte spatial

        Args:
            clickable_elements: Liste des détections OmniParser
                                (avec au moins: id, bbox, center, description/label, confidence)
            ocr_results: Détections OCR Paddle ({text, bbox, center, confidence})
            image_shape: (height, width)
            context: "browser", "desktop", "app"

        Returns:
            Liste enrichie, chaque élément type:

            {
              "id": 26,
              "visual_description": "magnifying glass icon",
              "ocr_nearby": "Rechercher sur Google ou saisir",
              "functional_type": "input",
              "function": "search_or_zoom",
              "spatial_context": "browser toolbar",
              "enriched_description": "Search/Zoom input field in browser toolbar with text: Rechercher sur Google ou saisir",
              "position": [752, 63],
              "center": (752, 63),
              "bbox": [x, y, w, h],
              "confidence": 0.68,
              "label": "...",
              "description": "..."    # description enrichie (pour l'annotateur / log)
            }
        """
        if not clickable_elements:
            return []

        print(
            f"[SemanticEnricher] Enrichissement de {len(clickable_elements)} éléments..."
        )

        enriched: List[Dict] = []

        for elem_idx, elem in enumerate(clickable_elements):
            elem_id = elem.get("id", elem_idx)

            raw_visual_desc = elem.get("description", elem.get("label", "UI Element"))
            visual_desc = self._normalize_visual_description(raw_visual_desc)

            bbox = elem.get("bbox", [0, 0, 0, 0])
            center = elem.get("center", (0, 0))
            cx, cy = center
            confidence = float(elem.get("confidence", 0.0))

            # 1. Texte OCR à proximité
            ocr_nearby = self._find_nearby_ocr(bbox, center, ocr_results)

            # 2. Contexte spatial
            spatial_context = self._get_spatial_context(center, image_shape, context)

            # 3. Classification fonctionnelle
            functional_type, function = self._classify_by_pattern(visual_desc)

            # 3.bis: heuristique sur flèches sans direction explicite
            if (
                "arrow" in visual_desc.lower()
                and function in ("unknown", "navigation", "direction")
                and image_shape is not None
            ):
                h, w = image_shape
                if cx < w * 0.25 and "browser" in spatial_context:
                    function = "back"
                    functional_type = "button"
                elif cx > w * 0.75 and "browser" in spatial_context:
                    function = "forward"
                    functional_type = "button"

            # 3.ter: heuristiques sur champ de recherche
            if function in ("search", "search_or_zoom") and ocr_nearby:
                lower = ocr_nearby.lower()
                if any(
                    kw in lower
                    for kw in [
                        "rechercher",
                        "search",
                        "saisir",
                        "type here",
                        "search or type",
                    ]
                ):
                    functional_type = "input"

            # 4. Description enrichie finale
            enriched_desc = self._generate_enriched_description(
                visual_desc=visual_desc,
                ocr_nearby=ocr_nearby,
                functional_type=functional_type,
                function=function,
                spatial_context=spatial_context,
            )

            # 5. Construire l'élément enrichi
            pos_list = [int(cx), int(cy)]

            label = ocr_nearby or visual_desc or elem.get("label", "element")

            enriched_elem: Dict = {
                "id": elem_id,
                "visual_description": visual_desc,
                "ocr_nearby": ocr_nearby,
                "functional_type": functional_type,
                "function": function,
                "spatial_context": spatial_context,
                "enriched_description": enriched_desc,
                "position": pos_list,
                "center": center,
                "bbox": bbox,
                "confidence": confidence,
                # Pour compatibilité avec annotateur / pipeline existant
                "label": label,
                "description": enriched_desc,
                "raw_label": elem.get("label"),
                "raw_description": elem.get("description"),
            }

            enriched.append(enriched_elem)
            print(f"  [SemanticEnricher] ID {elem_id}: {enriched_desc[:120]}")

        print(f"[SemanticEnricher] Terminé: {len(enriched)} éléments enrichis\n")
        return enriched

    def _normalize_visual_description(self, caption: str) -> str:
        """
        Nettoie la caption OmniParser pour en faire une description visuelle courte.
        Exemple:
          "A black and white image of a magnifying glass."
          -> "magnifying glass icon"
        """
        if not caption:
            return "UI element"

        text = caption.strip()

        # Normalisation simple
        lower = text.lower()

        if "magnifying glass" in lower:
            return "magnifying glass icon"
        if "arrow" in lower and "left" in lower:
            return "left arrow icon"
        if "arrow" in lower and "right" in lower:
            return "right arrow icon"
        if "arrow" in lower:
            return "arrow icon"
        if "cross" in lower or ' "x" ' in lower or " x " in lower:
            return "x icon"
        if "star" in lower:
            return "star icon"
        if "folder" in lower:
            return "folder icon"
        if "logo" in lower:
            return "logo"
        if "circle" in lower and "letter" in lower:
            return "letter in circle icon"

        # Fallback: enlever le début "A " / "An " / "The "
        text = re.sub(r"^(A|An|The)\s+", "", text, flags=re.IGNORECASE)
        return text

    def _find_nearby_ocr(
        self,
        bbox: List[int],
        center: Tuple[int, int],
        ocr_results: List[Dict],
        threshold: int = 50,
    ) -> Optional[str]:
        """
        Fusionne TOUS les textes OCR dont le centre est dans la bbox OmniParser
        Stratégie inspirée d'OmniParser (Microsoft Research)
        """
        if not ocr_results:
            return None

        x, y, w, h = bbox
        cx, cy = center

        # Collecte TOUS les textes OCR dont le centre est dans la bbox
        texts_inside = []

        for ocr in ocr_results:
            ocr_text = ocr.get("text", "").strip()
            if not ocr_text:
                continue

            ocr_bbox = ocr.get("bbox", [])
            if len(ocr_bbox) < 4:
                continue

            ox, oy, ow, oh = ocr_bbox
            
            # Calculer le centre de la bbox OCR
            ocr_cx = ox + ow // 2
            ocr_cy = oy + oh // 2

            # Si le CENTRE de l'OCR est dans la bbox OmniParser
            if x <= ocr_cx <= (x + w) and y <= ocr_cy <= (y + h):
                texts_inside.append((oy, ocr_text))

        # Si on a trouvé du texte dedans, fusionner tous les textes
        if texts_inside:
            # Trier par position Y (haut en bas)
            texts_inside.sort(key=lambda t: t[0])
            # Fusionner avec espace
            return " ".join([t[1] for t in texts_inside])

        # Sinon, chercher le plus proche (fallback)
        best_text = None
        min_distance = float("inf")

        for ocr in ocr_results:
            ocr_text = ocr.get("text", "").strip()
            if not ocr_text:
                continue

            ocr_bbox = ocr.get("bbox", [])
            if len(ocr_bbox) < 4:
                continue

            ox, oy, ow, oh = ocr_bbox
            ocr_cx = ox + ow // 2
            ocr_cy = oy + oh // 2

            # Distance centre-centre
            distance = np.sqrt((cx - ocr_cx) ** 2 + (cy - ocr_cy) ** 2)

            if distance < min_distance and distance < threshold:
                min_distance = distance
                best_text = ocr_text

        return best_text

    def _classify_by_pattern(self, visual_desc: str) -> Tuple[str, str]:
        """
        Classifie l'élément selon patterns visuels
        Retourne (functional_type, function)
        """
        visual_lower = visual_desc.lower()
        detected_function = "unknown"
        functional_type = "element"

        # Matching direct avec VISUAL_PATTERNS
        for pattern, functions in self.VISUAL_PATTERNS.items():
            if pattern in visual_lower:
                detected_function = functions[0]

                if any(word in visual_lower for word in ["button", "icon", "click"]):
                    functional_type = "button"
                elif "logo" in functions or "branding" in functions:
                    functional_type = "logo"
                elif any(word in visual_lower for word in ["field", "input", "bar", "box"]):
                    functional_type = "input"
                elif any(word in visual_lower for word in ["link", "text"]):
                    functional_type = "link"
                else:
                    functional_type = "button"
                break

        # Heuristiques supplémentaires
        if "search" in visual_lower or "recherch" in visual_lower:
            detected_function = "search"
            if any(kw in visual_lower for kw in ["bar", "field", "box", "input"]):
                functional_type = "input"
            else:
                functional_type = "button"

        if "close" in visual_lower or "fermer" in visual_lower:
            detected_function = "close"
            functional_type = "button"

        return functional_type, detected_function

    def _get_spatial_context(
        self,
        center: Tuple[int, int],
        image_shape: Optional[Tuple[int, int]],
        context: str = "browser",
    ) -> str:
        """
        Détermine le contexte spatial ("browser toolbar", "browser controls", etc.)
        """
        if image_shape is None:
            return "unknown"

        height, width = image_shape
        cx, cy = center

        top_zone = height * 0.15
        bottom_zone = height * 0.85
        left_zone = width * 0.25
        right_zone = width * 0.75

        if cy < top_zone:
            if cx < left_zone:
                zone = "top-left"
            elif cx > right_zone:
                zone = "top-right"
            else:
                zone = "top-center"
        elif cy > bottom_zone:
            zone = "bottom"
        else:
            zone = "center"

        if context == "browser":
            return self.SPATIAL_CONTEXTS_BROWSER.get(zone, zone)
        else:
            return zone

    def _generate_enriched_description(
        self,
        visual_desc: str,
        ocr_nearby: Optional[str],
        functional_type: str,
        function: str,
        spatial_context: str,
    ) -> str:
        """
        Génère la description enrichie finale.

        Exemples:
        - "Search/Zoom button in browser toolbar with text: Rechercher sur Google ou saisir"
        - "Close button (closes current tab or window) in browser controls"
        - "Back navigation button in browser navigation"
        """
        parts: List[str] = []

        func_lower = function.lower()

        if func_lower in ("search", "search_or_zoom"):
            label = "Search"
            if func_lower == "search_or_zoom":
                label = "Search/Zoom"

            if functional_type == "input":
                label += " input field"
            else:
                label += " button"

            parts.append(label)

        elif func_lower == "close":
            label = "Close button"
            if "browser controls" in spatial_context:
                label += " (closes current tab or window)"
            parts.append(label)

        elif func_lower in ("back", "previous"):
            label = "Back navigation button"
            parts.append(label)

        elif func_lower in ("forward", "next"):
            label = "Forward navigation button"
            parts.append(label)

        elif functional_type == "logo":
            if visual_desc:
                parts.append(f"{visual_desc} (branding element, not interactive)")
            else:
                parts.append("Branding/logo element")

        else:
            if function != "unknown":
                if functional_type == "input":
                    parts.append(f"{function.capitalize()} input field")
                elif functional_type == "button":
                    parts.append(f"{function.capitalize()} button")
                elif functional_type == "link":
                    parts.append(f"{function.capitalize()} link")
                else:
                    parts.append(f"{function.capitalize()} {functional_type}")
            else:
                if visual_desc:
                    parts.append(visual_desc)
                else:
                    parts.append(functional_type.capitalize())

        # Ajout de la description visuelle si elle n'est pas déjà incluse
        if visual_desc and visual_desc not in parts[0]:
            visual_short = visual_desc[:80]
            parts.append(f"({visual_short})")

        if ocr_nearby:
            parts.append(f"with text: {ocr_nearby}")

        if spatial_context and spatial_context != "unknown":
            parts.append(f"in {spatial_context}")

        enriched = " ".join(parts)
        enriched = re.sub(r"\s+", " ", enriched).strip()
        return enriched

    def format_for_llm(self, enriched_elements: List[Dict], max_items: int = 50) -> str:
        """
        Formate les éléments enrichis pour le VLM

        Format:
          ID, description enrichie, position, confiance
        """
        if not enriched_elements:
            return "Aucun élément cliquable détecté."

        lines = ["ÉLÉMENTS CLIQUABLES DÉTECTÉS:\n"]

        for elem in enriched_elements[:max_items]:
            elem_id = elem["id"]
            enriched_desc = elem["enriched_description"]
            cx, cy = elem["position"]
            conf = elem["confidence"]

            line = f"  ID {elem_id}: {enriched_desc}"
            line += f" | Position: ({cx}, {cy})"
            line += f" | Confiance: {conf:.2f}"

            lines.append(line)

        if len(enriched_elements) > max_items:
            lines.append(
                f"\n  ... et {len(enriched_elements) - max_items} autres éléments"
            )

        return "\n".join(lines)


# Instance globale
semantic_enricher = SemanticEnricher()
