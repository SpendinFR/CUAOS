from utils.ollama_client import OllamaClient

class Verificateur:
    def __init__(self):
        self.client = OllamaClient()
    
    def verifier(self, tache, resultat):
        # 🔥 DÉTECTION AUTOMATIQUE DES SUCCÈS
        description = tache['description'].lower()
        resultat_str = str(resultat).lower()
        
        # Si c'est une commande "start" et qu'on a pas d'erreur évidente
        if "start" in resultat_str and "erreur" not in resultat_str and "n'est pas reconnu" not in resultat_str:
            print("✅ Succès détecté automatiquement (commande start)")
            return True
        
        # Si le code retour est 0
        if "code: 0" in resultat_str:
            print("✅ Succès détecté automatiquement (code 0)")
            return True
        
        # Si la commande a été lancée en arrière-plan
        if "commande lancée" in resultat_str:
            print("✅ Succès détecté automatiquement (commande lancée)")
            return True
        
        # Fallback: vérification par LLM
        prompt = f"""
        Tâche: {tache['description']}
        Résultat: {resultat}
        
        La tâche est-elle accomplie avec succès?
        Pour les commandes 'start' qui lancent des applications, considère que c'est réussi si l'application s'ouvre.
        
        Réponds uniquement par OUI ou NON.
        """
        reponse = self.client.generate(prompt).strip().upper()
        print(f"🔍 Vérification LLM: {reponse}")
        return reponse == "OUI"