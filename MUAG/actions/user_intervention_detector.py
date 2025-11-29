"""
User Intervention Detector pour CUA Agent
Détecte automatiquement quand l'utilisateur doit intervenir (CAPTCHA, MDP, confirmations)
"""
from typing import Dict, Optional


class UserInterventionDetector:
    """Détecteur d'interventions utilisateur nécessaires"""
    
    def __init__(self, use_vlm_validation=False):
        """
        Args:
            use_vlm_validation: Utiliser VLM pour valider (plus lent mais plus précis)
        """
        self.use_vlm_validation = use_vlm_validation
        
        # Import config
        from config import (
            REQUIRE_CONFIRMATION_EMAIL,
            REQUIRE_CONFIRMATION_PURCHASE,
            REQUIRE_CONFIRMATION_FILE_DELETE,
            USER_INTERVENTION_KEYWORDS_CAPTCHA,
            USER_INTERVENTION_KEYWORDS_PASSWORD
        )
        
        self.require_email_confirm = REQUIRE_CONFIRMATION_EMAIL
        self.require_purchase_confirm = REQUIRE_CONFIRMATION_PURCHASE
        self.require_delete_confirm = REQUIRE_CONFIRMATION_FILE_DELETE
        
        # Ajout du flag download si disponible
        try:
            from config import REQUIRE_CONFIRMATION_DOWNLOAD
            self.require_download_confirm = REQUIRE_CONFIRMATION_DOWNLOAD
        except ImportError:
            self.require_download_confirm = False
        
        self.captcha_keywords = USER_INTERVENTION_KEYWORDS_CAPTCHA
        self.password_keywords = USER_INTERVENTION_KEYWORDS_PASSWORD
    
    def detect_intervention_needed(
        self, 
        screenshot_path: str, 
        page_text: str, 
        vlm_description: str, 
        planned_action: Dict
    ) -> Dict:
        """
        Détecte si une intervention utilisateur est nécessaire
        
        Returns:
            {
                "needed": bool,
                "reason": "captcha"|"password"|"confirmation"|"error"|None,
                "confidence": float,
                "message": str
            }
        """
        # 1. Détection CAPTCHA (prioritaire)
        captcha_result = self._detect_captcha(page_text, vlm_description)
        if captcha_result["needed"]:
            return captcha_result
        
        # 2. Détection mot de passe
        password_result = self._detect_password(page_text, vlm_description)
        if password_result["needed"]:
            return password_result
        
        # 3. Détection confirmations (achat, suppression, téléchargement)
        confirmation_result = self._detect_confirmation(page_text, planned_action)
        if confirmation_result["needed"]:
            return confirmation_result
        
        # 4. Détection erreurs bloquantes
        error_result = self._detect_error(page_text, vlm_description)
        if error_result["needed"]:
            return error_result
        
        # Aucune intervention nécessaire
        return {"needed": False, "reason": None, "confidence": 0.0, "message": ""}
    
    def _detect_captcha(self, page_text: str, vlm_description: str) -> Dict:
        """Détecte la présence d'un CAPTCHA"""
        page_lower = page_text.lower()
        vlm_lower = vlm_description.lower()
        
        # Heuristique: mots-clés CAPTCHA
        for keyword in self.captcha_keywords:
            if keyword in page_lower or keyword in vlm_lower:
                return {
                    "needed": True,
                    "reason": "captcha",
                    "confidence": 0.9,
                    "message": "CAPTCHA détecté - résolvez-le manuellement"
                }
        
        return {"needed": False, "reason": None, "confidence": 0.0, "message": ""}
    
    def _detect_password(self, page_text: str, vlm_description: str) -> Dict:
        """Détecte un champ de mot de passe"""
        page_lower = page_text.lower()
        vlm_lower = vlm_description.lower()
        
        # Heuristique: mots-clés password
        password_found = any(kw in page_lower or kw in vlm_lower for kw in self.password_keywords)
        
        if password_found:
            return {
                "needed": True,
                "reason": "password",
                "confidence": 0.8,
                "message": "Champ mot de passe détecté - entrez vos identifiants"
            }
        
        return {"needed": False, "reason": None, "confidence": 0.0, "message": ""}
    
    def _detect_confirmation(self, page_text: str, planned_action: Dict) -> Dict:
        """Détecte si une confirmation utilisateur est requise"""
        action_str = str(planned_action).lower() if planned_action else ""
        
        # Achat
        if self.require_purchase_confirm:
            purchase_keywords = ["acheter", "payer", "buy", "checkout", "payment", "confirm payment"]
            if any(kw in action_str for kw in purchase_keywords):
                return {
                    "needed": True,
                    "reason": "confirmation",
                    "confidence": 0.95,
                    "message": "Confirmation requise avant achat"
                }
        
        # Téléchargement
        if self.require_download_confirm:
            download_keywords = ["download", "télécharger", "save file", "enregistrer"]
            if any(kw in action_str for kw in download_keywords):
                return {
                    "needed": True,
                    "reason": "confirmation",
                    "confidence": 0.9,
                    "message": "Confirmation requise avant téléchargement"
                }
        
        # Suppression
        if self.require_delete_confirm:
            delete_keywords = ["delete", "supprimer", "remove", "trash", "permanently delete"]
            if any(kw in action_str for kw in delete_keywords):
                return {
                    "needed": True,
                    "reason": "confirmation",
                    "confidence": 0.95,
                    "message": "Confirmation requise avant suppression"
                }
        
        # Email
        if self.require_email_confirm:
            email_keywords = ["send", "envoyer", "send email", "envoyer email"]
            if any(kw in action_str for kw in email_keywords):
                return {
                    "needed": True,
                    "reason": "confirmation",
                    "confidence": 0.9,
                    "message": "Confirmation requise avant envoi d'email"
                }
        
        return {"needed": False, "reason": None, "confidence": 0.0, "message": ""}
    
    def _detect_error(self, page_text: str, vlm_description: str) -> Dict:
        """Détecte des erreurs bloquantes"""
        page_lower = page_text.lower()
        vlm_lower = vlm_description.lower()
        
        error_keywords = [
            "access denied", "accès refusé",
            "incorrect password", "mot de passe incorrect",
            "error", "erreur",
            "failed", "échec", "échoué",
            "not authorized", "non autorisé"
        ]
        
        for keyword in error_keywords:
            if keyword in page_lower or keyword in vlm_lower:
                return {
                    "needed": True,
                    "reason": "error",
                    "confidence": 0.7,
                    "message": f"Erreur détectée: vérifiez l'écran"
                }
        
        return {"needed": False, "reason": None, "confidence": 0.0, "message": ""}
