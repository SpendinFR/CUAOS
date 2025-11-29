"""
User Profile - Profil utilisateur intelligent construit par LLM
"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class UserProfile:
    """
    Profil utilisateur intelligent construit et mis à jour par LLM
    
    Structure:
    {
        "preferences": {
            "tone": "casual|formal|friendly",
            "interaction_style": "direct|explanatory|detailed",
            "favorites": {"music": "Spotify", "browser": "Chrome", ...}
        },
        "habits": {
            "work_hours": "9-17",
            "frequent_actions": ["ouvre Spotify", "va sur YouTube"],
            "patterns": ["Travaille souvent le soir", ...]
        },
        "context": {
            "recent_activities": [...],
            "ongoing_projects": [...],
            "last_session_summary": "..."
        },
        "personality_notes": [
            "Préfère les réponses courtes",
            "Aime qu'on lui rappelle ce qu'il a fait",
            ...
        ]
    }
    """
    
    def __init__(self, llm_client):
        """
        Args:
            llm_client: Instance OllamaClient pour analyse LLM
        """
        self.llm = llm_client
        self.profile_file = Path("data/user_profile.json")
        self.profile = self.load_profile()
    
    def load_profile(self) -> Dict:
        """Charge le profil depuis le fichier"""
        
        default_profile = {
            "preferences": {
                "tone": "friendly",
                "interaction_style": "balanced",
                "favorites": {}
            },
            "habits": {
                "frequent_actions": [],
                "patterns": []
            },
            "context": {
                "recent_activities": [],
                "ongoing_projects": [],
                "last_session_summary": ""
            },
            "personality_notes": [],
            "last_updated": datetime.now().isoformat()
        }
        
        if self.profile_file.exists():
            try:
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                
                # Merge avec structure par défaut (pour nouvelles clés)
                for key, value in default_profile.items():
                    if key not in profile:
                        profile[key] = value
                
                return profile
            except Exception as e:
                print(f"[Profile] Erreur chargement: {e}")
                return default_profile
        
        return default_profile
    
    def save_profile(self):
        """Sauvegarde le profil"""
        try:
            self.profile["last_updated"] = datetime.now().isoformat()
            self.profile_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Profile] Erreur sauvegarde: {e}")
    
    def update_from_interaction(self, requete: str, reponse: str):
        """
        Met à jour le profil basé sur une interaction
        LLM analyse et extrait insights
        
        Args:
            requete: Requête utilisateur
            reponse: Réponse de l'agent
        """
        
        prompt = f"""Analyse cette interaction pour mettre à jour le profil utilisateur.

INTERACTION:
User: {requete}
Agent: {reponse[:500]}

PROFIL ACTUEL:
{json.dumps(self.profile, ensure_ascii=False, indent=2)[:1500]}

Extrais et mets à jour:
1. Préférences (ton préféré, style interaction, favoris)
2. Habitudes (actions fréquentes, patterns de comportement)
3. Contexte (activités récentes, projets en cours)
4. Notes personnalité (ce qui caractérise l'utilisateur)

Retourne UNIQUEMENT JSON avec les mises à jour (vide si rien):
{{
    "preferences": {{...}},
    "habits": {{...}},
    "context": {{...}},
    "personality_notes": [...]
}}

Si aucune mise à jour nécessaire, retourne {{}}.
"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=500, temperature=0.3)
            updates = json.loads(self._extract_json(response))
            
            if updates:
                self._merge_updates(updates)
                self.save_profile()
                print(f"[Profile] Mis à jour")
                
        except Exception as e:
            # Silencieux - pas critique si ça échoue
            pass
    
    def get_contextual_information(self, current_request: str) -> str:
        """
        LLM décide quelle information du profil est pertinente
        
        Args:
            current_request: Requête actuelle de l'utilisateur
        
        Returns:
            Information pertinente du profil ou chaîne vide
        """
        
        prompt = f"""Requête utilisateur: {current_request}

PROFIL USER:
{json.dumps(self.profile, ensure_ascii=False, indent=2)[:1000]}

Quelle information du profil est PERTINENTE pour cette requête?

Exemples:
- Si user demande Spotify et favoris music = "Spotify" → pertinent
- Si user demande nouvel outil et jamais utilisé → non pertinent
- Si pattern comportemental utile → pertinent

Retourne JSON:
{{
    "relevant": true|false,
    "info": "contexte pertinent court (1-2 phrases)",
    "reason": "pourquoi"
}}

Si rien pertinent, retourne {{"relevant": false}}.
"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=300, temperature=0.2)
            result = json.loads(self._extract_json(response))
            
            if result.get("relevant"):
                return result.get("info", "")
            
        except Exception as e:
            pass
        
        return ""
    
    def get_tone_preference(self) -> str:
        """Obtient le ton préféré de l'utilisateur"""
        return self.profile["preferences"].get("tone", "friendly")
    
    def get_interaction_style(self) -> str:
        """Obtient le style d'interaction préféré"""
        return self.profile["preferences"].get("interaction_style", "balanced")
    
    def add_recent_activity(self, activity: str):
        """Ajoute une activité récente"""
        activities = self.profile["context"]["recent_activities"]
        activities.append({
            "activity": activity,
            "timestamp": datetime.now().isoformat()
        })
        
        # Garder seulement les 20 dernières
        self.profile["context"]["recent_activities"] = activities[-20:]
        self.save_profile()
    
    def _extract_json(self, text: str) -> str:
        """Extrait JSON d'une réponse LLM"""
        # Nettoyer markdown
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Trouver JSON dans le texte
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if match:
            return match.group()
        
        return text
    
    def _merge_updates(self, updates: Dict):
        """Fusionne les mises à jour dans le profil"""
        
        for key, value in updates.items():
            if key in self.profile:
                if isinstance(value, dict) and isinstance(self.profile[key], dict):
                    # Fusion dict
                    self.profile[key].update(value)
                elif isinstance(value, list) and isinstance(self.profile[key], list):
                    # Ajout liste (éviter doublons)
                    for item in value:
                        if item not in self.profile[key]:
                            self.profile[key].append(item)
                else:
                    # Remplacement direct
                    self.profile[key] = value
