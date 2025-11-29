"""
Memory Manager - Gestion avancée de la mémoire avec moments marquants
"""
import json
import os
from datetime import datetime
from pathlib import Path
from config import (
    MEMORY_FILE,
    PREFERENCES_FILE,
    MAX_MEMORY_INTERACTIONS,
    MAX_CONTEXT_INTERACTIONS,
    DETECT_IMPORTANT_MOMENTS,
    IMPORTANT_MOMENT_KEYWORDS
)
from utils.ollama_client import OllamaClient


class MemoryManager:
    def __init__(self):
        self.client = OllamaClient()
        self.memory_file = Path(MEMORY_FILE)
        self.preferences_file = Path(PREFERENCES_FILE)
        self.memoire = self.charger_memoire()
        self.preferences = self.charger_preferences()
    
    def charger_memoire(self):
        """Charge la mémoire depuis le fichier"""
        default_structure = {
            "interactions": [],
            "moments_marquants": [],
            "connaissances": {}
        }
        
        if self.memory_file.exists():
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                memoire = json.load(f)
                
            # S'assurer que toutes les clés nécessaires existent
            for key, default_value in default_structure.items():
                if key not in memoire:
                    memoire[key] = default_value
            
            return memoire
        
        return default_structure
    
    def charger_preferences(self):
        """Charge les préférences utilisateur"""
        if self.preferences_file.exists():
            with open(self.preferences_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "favoris": {},
            "ton_prefere": "naturel",
            "personnalite_agent": "helpful",
            "confirmations": {
                "email": True,
                "achat": True,
                "suppression_fichier": True
            }
        }
    
    def sauvegarder_memoire(self):
        """Sauvegarde la mémoire"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memoire, f, ensure_ascii=False, indent=2)
    
    def sauvegarder_preferences(self):
        """Sauvegarde les préférences"""
        with open(self.preferences_file, 'w', encoding='utf-8') as f:
            json.dump(self.preferences, f, ensure_ascii=False, indent=2)
    
    def sauvegarder_interaction(self, requete, resultats):
        """Sauvegarde une interaction"""
        interaction = {
            "requete": requete,
            "resultats": resultats,
            "timestamp": datetime.now().isoformat()
        }
        self.memoire["interactions"].append(interaction)
        
        if DETECT_IMPORTANT_MOMENTS:
            moment_data = self.detect_important_moment_llm(requete, resultats)
            if moment_data.get("important", False):
                self.ajouter_moment_marquant(requete, resultats, moment_data)
        

        # Limiter la taille de la mémoire
        if len(self.memoire["interactions"]) > MAX_MEMORY_INTERACTIONS:
            self.memoire["interactions"] = self.memoire["interactions"][-MAX_MEMORY_INTERACTIONS:]
        
        self.sauvegarder_memoire()

        
    def detect_important_moment_llm(self, requete: str, resultats: dict) -> dict:
        """Détection LLM de moments importants (remplace heuristiques)"""
        
        prompt = f"""Analyse cette interaction.

INTERACTION:
Requête: {requete}
Résultat: {str(resultats)[:500]}

Est-ce un MOMENT IMPORTANT à retenir long-terme?

Exemples moments importants:
- Nouvelles préférences exprimées
- Accomplissements significatifs
- Informations personnelles importantes
- Patterns de comportement émergents

Retourne UNIQUEMENT JSON:
{{
    "important": true|false,
    "importance": 1-10,
    "reason": "pourquoi important",
    "category": "preference|accomplishment|personal|pattern|other"
}}
"""
        
        try:
            response = self.client.generate(prompt, max_tokens=200, temperature=0.3)
            import re
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            pass
        
        return {"important": False}
    
    def ajouter_moment_marquant(self, requete, resultats, moment_data: dict):
        """Ajoute un moment marquant avec données LLM"""
        moment = {
            "requete": requete,
            "resultats": resultats,
            "timestamp": datetime.now().isoformat(),
            "importance": moment_data.get("importance", 5),
            "category": moment_data.get("category", "other"),
            "reason": moment_data.get("reason", "")
        }
        self.memoire["moments_marquants"].append(moment)
        print(f"⭐ Moment marquant: {requete[:50]}... ({moment_data.get('category')})")
    
    def consolidate_session(self) -> str:
        """Consolidation session avec LLM (appelé à la fermeture)"""
        
        recent = self.memoire["interactions"][-50:]
        
        if not recent:
            return ""
        
        prompt = f"""Résume cette session de travail.

{len(recent)} INTERACTIONS:
{json.dumps(recent, ensure_ascii=False, indent=2)[:3000]}

Génère résumé structuré JSON:
{{
    "summary": "résumé court",
    "key_activities": ["activité 1", "activité 2"],
    "notable_moments": ["moment 1"],
    "user_mood": "mood/état",
    "next_session_context": "utile pour prochaine fois"
}}
"""
        
        try:
            response = self.client.generate(prompt, max_tokens=600, temperature=0.3)
            import re
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if match:
                consolidation = json.loads(match.group())
                
                # Sauvegarder
                if "consolidations" not in self.memoire:
                    self.memoire["consolidations"] = []
                
                self.memoire["consolidations"].append({
                    "timestamp": datetime.now().isoformat(),
                    "consolidation": consolidation
                })
                
                # Max 30 consolidations
                self.memoire["consolidations"] = self.memoire["consolidations"][-30:]
                
                self.sauvegarder_memoire()
                
                return consolidation.get("summary", "")
                
        except Exception as e:
            print(f"[Memory] Erreur consolidation: {e}")
        
        return ""
    
    def get_contexte_recent(self, requete_actuelle: str = "") -> str:
        """Génère contexte pertinent avec LLM"""
        
        recent = self.memoire["interactions"][-MAX_CONTEXT_INTERACTIONS:]
        
        if not recent:
            return ""
        
        # Dernière consolidation
        last_consolidation = ""
        if self.memoire.get("consolidations"):
            last_consolidation = self.memoire["consolidations"][-1].get("consolidation", "")
        
        # Profil (si disponible)
        profile_info = ""
        if hasattr(self, 'user_profile'):
            profile_info = json.dumps(self.user_profile.profile, ensure_ascii=False)[:500]
        
        prompt = f"""Génère CONTEXTE PERTINENT pour cette requête.

REQUÊTE: {requete_actuelle}

HISTORIQUE RÉCENT:
{json.dumps(recent, ensure_ascii=False, indent=2)[:1500]}

DERNIÈRE SESSION:
{str(last_consolidation)[:500]}

PROFIL:
{profile_info}

Génère contexte CONCIS (2-3 phrases max):
1. Rappelle UNIQUEMENT ce qui est pertinent
2. Patterns/habitudes utiles
3. Rappel naturel si approprié

Si RIEN pertinent, retourne chaîne vide.
"""
        
        try:
            context = self.client.generate(prompt, max_tokens=200, temperature=0.3)
            return context.strip()
        except:
            return ""
    
    def get_moments_pertinents(self, requete):
        """Récupère les moments marquants pertinents"""
        if not requete or not self.memoire["moments_marquants"]:
            return []
        
        # Filtrer par pertinence (simple matching de mots-clés)
        pertinents = []
        mots_cles = set(requete.lower().split())
        
        for moment in self.memoire["moments_marquants"]:
            mots_moment = set(moment['requete'].lower().split())
            if mots_cles & mots_moment:  # Intersection
                pertinents.append(moment)
        
        # Trier par importance
        pertinents.sort(key=lambda x: x.get('importance', 5), reverse=True)
        return pertinents
    
    def get_similar_interactions(self, requete):
        """Trouve les interactions similaires"""
        similaires = []
        mots_cles = set(requete.lower().split())
        
        for interaction in self.memoire["interactions"]:
            mots_interaction = set(interaction['requete'].lower().split())
            similarite = len(mots_cles & mots_interaction) / max(len(mots_cles), 1)
            
            if similarite > 0.3:
                similaires.append({
                    'interaction': interaction,
                    'similarite': similarite
                })
        
        similaires.sort(key=lambda x: x['similarite'], reverse=True)
        return [s['interaction'] for s in similaires[:3]]
    
    def get_preference(self, categorie):
        """Récupère une préférence spécifique"""
        return self.preferences["favoris"].get(categorie)
    
    def set_preference(self, categorie, valeur):
        """Définit une préférence"""
        self.preferences["favoris"][categorie] = valeur
        self.sauvegarder_preferences()