import json
import re
from utils.ollama_client import OllamaClient

class Decomposeur:
    def __init__(self):
        self.client = OllamaClient()
    
    def analyser_dependances(self, plan):
        # Détection automatique de la complexité
        lignes_plan = plan.split('\n')
        etapes = [l for l in lignes_plan if re.match(r'^\d+\.', l)]
        
        if len(etapes) == 1:
            # Plan simple - pas besoin de décomposition complexe
            description = etapes[0].split('.', 1)[1].strip()
            return {
                "taches": {
                    "tache_1": {
                        "description": description,
                        "dependances": [],
                        "type": "action_simple"
                    }
                },
                "ordre_execution": ["tache_1"]
            }
        else:
            # Plan complexe - analyse des dépendances
            return self.analyser_plan_complexe(plan)
    
    def analyser_plan_complexe(self, plan):
        prompt = f"""
        Plan: {plan}
        
        Analyse les dépendances entre ces étapes. Identifie:
        - Quelles étapes doivent être faites en premier
        - Les dépendances entre étapes
        - L'ordre logique d'exécution
        
        Retourne du JSON:
        {{
            "taches": {{
                "tache_1": {{
                    "description": "...",
                    "dependances": [],
                    "type": "action"
                }}
            }},
            "ordre_execution": ["tache_1", "tache_2"]
        }}
        """
        
        reponse = self.client.generate(prompt)
        json_match = re.search(r'\{.*\}', reponse, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Fallback pour plans complexes
        return self.fallback_plan_complexe(plan)
    
    def fallback_plan_complexe(self, plan):
        """Fallback simple pour les plans complexes"""
        lignes = plan.split('\n')
        etapes = [l.strip() for l in lignes if re.match(r'^\d+\.', l)]
        
        taches = {}
        for i, etape in enumerate(etapes, 1):
            tache_id = f"tache_{i}"
            description = etape.split('.', 1)[1].strip()
            
            taches[tache_id] = {
                "description": description,
                "dependances": [f"tache_{j}" for j in range(1, i)] if i > 1 else [],
                "type": "action"
            }
        
        return {
            "taches": taches,
            "ordre_execution": list(taches.keys())
        }