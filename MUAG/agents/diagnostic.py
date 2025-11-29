from utils.ollama_client import OllamaClient

class AgentDiagnostic:
    def __init__(self):
        self.client = OllamaClient()
    
    def analyser_erreur_systeme(self, tache, erreur):
        prompt = f"""
        Tâche: {tache}
        Erreur: {erreur}
        
        Diagnostique le problème et propose une solution.
        Sois concis.
        """
        return self.client.generate(prompt)