from utils.ollama_client import OllamaClient

class Planificateur:
    def __init__(self):
        self.client = OllamaClient()
    
    def generer_plan(self, requete, contexte_historique):
        prompt = f"""
        CONTEXTE: {contexte_historique}
        
        REQUÊTE: "{requete}"
        
        DÉCOMPOSE la requête en actions SIMPLES et SÉPARÉES.
        Une action = une commande système unique.
        
        Règles:
        - "lance chrome et va sur google" → 2 actions séparées
        - "ouvre notepad puis écris bonjour" → 2 actions séparées  
        - Chaque action doit pouvoir s'exécuter indépendamment
        
        Exemples:
        Requête: "lance chrome et va sur google"
        → PLAN: 
        1. Lancer Chrome
        2. Aller sur Google.com
        
        Requête: "lance fortnite"
        → PLAN:
        1. Lancer Fortnite
        
        Format:
        PLAN:
        1. [Action simple]
        2. [Action simple]
        
        Sois PRÉCIS et SÉPARE les actions.
        """
        
        return self.client.generate(prompt)