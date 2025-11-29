"""
Intention Analyzer - Analyse l'intention de l'utilisateur
Détermine si la requête nécessite une réponse conversationnelle ou une action
"""
from utils.ollama_client import OllamaClient
from enum import Enum


class IntentionType(Enum):
    """Types d'intentions possibles"""
    CONVERSATION = "conversation"  # Simple réponse conversationnelle
    ACTION_SIMPLE = "action_simple"  # Action unique
    ACTION_COMPLEXE = "action_complexe"  # Série d'actions
    QUESTION_MEMOIRE = "question_memoire"  # Question sur l'historique
    COMMANDE_SYSTEME = "commande_systeme"  # Contrôle de l'agent


class IntentionAnalyzer:
    def __init__(self):
        self.client = OllamaClient()
    
    def analyser(self, requete_utilisateur, contexte=""):
        """
        Analyse l'intention de l'utilisateur
        Args:
            requete_utilisateur: texte de la requête
            contexte: contexte de conversation
        Returns:
            dict: {
                'type': IntentionType,
                'confiance': float,
                'action_requise': bool,
                'details': dict
            }
        """
        prompt = f"""Tu es un analyseur d'intentions pour un assistant vocal autonome.

Requête utilisateur: "{requete_utilisateur}"
Contexte: {contexte if contexte else "Aucun"}

Analyse cette requête et détermine son intention parmi:
1. CONVERSATION - Simple discussion, question générale, bavardage
2. ACTION_SIMPLE - Action système DIRECTE sans interaction (lancer app, ouvrir URL/fichier) : 1 seule action , si 2 actions ou plus alors ACTION_COMPLEXE
3. ACTION_COMPLEXE - Plusieurs actions : Navigation web + interactions (aller sur site, chercher, cliquer, remplir formulaire)
4. QUESTION_MEMOIRE - Question sur l'historique ou préférences mémorisées

⚠️ IMPORTANT:
- "Lance Spotify" uniquement = ACTION_SIMPLE (juste ouvrir l'app)
- "Lance Spotify ET Actions " = ACTION_COMPLEXE (app + interaction ou navigation)
- "Ouvre fichier.txt" = ACTION_SIMPLE (ouvrir fichier)
- "Va sur YouTube" = ACTION_COMPLEXE (naviguer + chercher)
- "Cherche X sur Google" = ACTION_COMPLEXE (navigation web + interaction)
- "Créé un fichier texte" = ACTION_COMPLEXE (nécessite création)
Réponds UNIQUEMENT avec ce format JSON:
{{
    "type": "conversation|action_simple|action_complexe|question_memoire|commande_systeme",
    "confiance": 0.0-1.0,
    "action_requise": true/false,
    "description": "brève description de ce qui est demandé"
}}

Exemples:
- "Comment vas-tu?" → {{"type": "conversation", "confiance": 0.95, "action_requise": false}}
- "Lance Spotify" → {{"type": "action_simple", "confiance": 0.98, "action_requise": true}}
- "Ouvre Chrome" → {{"type": "action_simple", "confiance": 0.98, "action_requise": true}}
- "Va sur YouTube et ouvre une vidéo de Messi" → {{"type": "action_complexe", "confiance": 0.95, "action_requise": true}}
- "Cherche la météo sur Google" → {{"type": "action_complexe", "confiance": 0.92, "action_requise": true}}
- "Réserve-moi un vol Paris-Londres" → {{"type": "action_complexe", "confiance": 0.92, "action_requise": true}}
- "Quel est mon film préféré?" → {{"type": "question_memoire", "confiance": 0.90, "action_requise": false}}
- "Pause" → {{"type": "commande_systeme", "confiance": 1.0, "action_requise": false}}
"""
        
        try:
            response = self.client.generate(prompt)
            
            # Extraire le JSON de la réponse
            import json
            import re
            
            # Chercher le JSON dans la réponse
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Parser directement si c'est du JSON pur
                result = json.loads(response)
            
            # Valider et structurer le résultat
            intention_type = result.get('type', 'conversation')
            # Normalisation pour éviter les erreurs d'accents (ex: action_complexé)
            if isinstance(intention_type, str):
                intention_type = intention_type.lower().replace('é', 'e').replace('è', 'e')
            confiance = float(result.get('confiance', 0.5))
            action_requise = result.get('action_requise', False)
            description = result.get('description', requete_utilisateur)
            
            return {
                'type': IntentionType(intention_type),
                'confiance': confiance,
                'action_requise': action_requise,
                'details': {
                    'description': description,
                    'requete_originale': requete_utilisateur
                }
            }
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'analyse d'intention: {e}")
            # Par défaut, traiter comme conversation
            return {
                'type': IntentionType.CONVERSATION,
                'confiance': 0.3,
                'action_requise': False,
                'details': {
                    'description': requete_utilisateur,
                    'requete_originale': requete_utilisateur,
                    'erreur': str(e)
                }
            }
    
    def est_action(self, intention):
        """Détermine si l'intention nécessite une action"""
        return intention.get('action_requise', False) or intention['type'] in [
            IntentionType.ACTION_SIMPLE,
            IntentionType.ACTION_COMPLEXE
        ]
    
    def est_conversation(self, intention):
        """Détermine si l'intention est conversationnelle"""
        return intention['type'] in [
            IntentionType.CONVERSATION,
            IntentionType.QUESTION_MEMOIRE
        ]
    
    def extraire_parametres_action(self, requete, intention):
        """
        Extrait les paramètres pour une action
        Returns:
            dict: paramètres extraits
        """
        if not self.est_action(intention):
            return {}
        
        prompt = f"""Extrais les paramètres de cette action:
"{requete}"

Type d'action: {intention['type'].value}

Retourne un JSON avec les paramètres pertinents:
- application/site/fichier concerné
- action à effectuer
- paramètres supplémentaires

Format JSON uniquement.
"""
        
        try:
            response = self.client.generate(prompt)
            import json
            import re
            
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}
            
        except Exception as e:
            print(f"⚠️ Erreur extraction paramètres: {e}")
            return {}
