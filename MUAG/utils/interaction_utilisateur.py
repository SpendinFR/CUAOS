class InterfaceUtilisateur:
    @staticmethod
    def afficher_alerte_blocage(tache, diagnostic, erreur):
        print(f"\n🚨 BLOCAGE: {tache}")
        print(f"🔧 {diagnostic}")
        print(f"📋 {erreur}")
    
    @staticmethod
    def demander_confirmation(message):
        while True:
            reponse = input(f"{message} (oui/non): ").lower().strip()
            if reponse in ['oui', 'o', 'yes', 'y']:
                return True
            elif reponse in ['non', 'n', 'no']:
                return False
            print("❌ Réponse invalide")