import json
from datetime import datetime
from .planificateur import Planificateur
from .decomposeur import Decomposeur
from .executeur import Executeur
from .verificateur import Verificateur
from .skill_manager import SkillManager
from .memory_manager import MemoryManager
from .intention_analyzer import IntentionAnalyzer, IntentionType
from utils.interaction_utilisateur import InterfaceUtilisateur
from utils.ollama_client import OllamaClient

class Coordinateur:
    def __init__(self):
        self.planificateur = Planificateur()
        self.decomposeur = Decomposeur()
        self.executeur = Executeur()
        self.verificateur = Verificateur()
        self.skill_manager = SkillManager()
        self.memory = MemoryManager()
        self.interface_utilisateur = InterfaceUtilisateur()
        self.intention_analyzer = IntentionAnalyzer()
        self.ollama_client = OllamaClient()
    
    def traiter_requete(self, requete_utilisateur):
        """
        Point d'entrée principal - décide entre répondre et agir
        """
        print(f"\n🔍 Analyse de: {requete_utilisateur}")
        
        # Obtenir le contexte
        contexte = self.memory.get_contexte_recent(requete_utilisateur)
        
        # Analyser l'intention
        intention = self.intention_analyzer.analyser(requete_utilisateur, contexte)
        print(f"💡 Intention détectée: {intention['type'].value} (confiance: {intention['confiance']:.2f})")
        
        # Décision: Répondre vs Agir
        if self.intention_analyzer.est_action(intention):
            # MODE ACTION
            return self.traiter_action(requete_utilisateur, intention, contexte)
        else:
            # MODE CONVERSATION
            return self.traiter_conversation(requete_utilisateur, intention, contexte)
    
    def traiter_conversation(self, requete, intention, contexte):
        """Traite une requête conversationnelle"""
        print("💬 Mode: CONVERSATION")
        
        # Si c'est une question mémoire, chercher dans les moments marquants
        if intention['type'] == IntentionType.QUESTION_MEMOIRE:
            moments = self.memory.get_moments_pertinents(requete)
            if moments:
                contexte += "\n\nMoments pertinents:\n"
                for moment in moments[:3]:
                    contexte += f"- {moment['requete']}\n"
        
        # Générer une réponse naturelle
        prompt = f"""Tu es un assistant vocal personnel amical et naturel.

Contexte: {contexte}

Utilisateur: "{requete}"

Génère une réponse naturelle, conversationnelle et personnalisée.
Si tu connais les préférences de l'utilisateur, utilise-les.
Sois concis mais chaleureux.
"""
        
        reponse = self.ollama_client.generate(prompt)
        
        # Sauvegarder l'interaction
        self.memory.sauvegarder_interaction(requete, {"type": "conversation", "reponse": reponse})
        
        return reponse
    
    def traiter_action(self, requete, intention, contexte):
        """Traite une requête nécessitant des actions"""
        print("🎬 Mode: ACTION")
        
        # Si ACTION_SIMPLE, exécuter directement sans planification
        if intention['type'] == IntentionType.ACTION_SIMPLE:
            print("⚡ Détection ACTION_SIMPLE → Exécution directe")
            return self.traiter_action_simple(requete, intention)

        # Si ACTION_COMPLEXE, router vers CUA
        if intention['type'] == IntentionType.ACTION_COMPLEXE:
            print("🤖 Détection ACTION_COMPLEXE → Routing vers CUA Agent")
            return self.traiter_avec_cua(requete, intention)

        # Sinon, traitement classique avec décomposition (pour compatibilité)
        interactions_similaires = self.memory.get_similar_interactions(requete)
                
        if interactions_similaires:
            print("📖 Interactions similaires trouvées")
        
        plan = self.planificateur.generer_plan(requete, contexte)
        print(f"📝 Plan: {plan}")
        
        graphe_taches = self.decomposeur.analyser_dependances(plan)
        resultats = self.executer_avec_reprise(graphe_taches)
        
        self.apprendre_et_memoriser(graphe_taches, resultats, requete)
        reponse = self.generer_reponse_contextuelle(requete, resultats)
        
        return reponse
    
    def traiter_avec_cua(self, requete, intention):
        """Traite une action complexe directement avec CUA Agent"""
        print(f"🎯 Lancement CUA pour: {requete}")
        
        # Créer une tâche unique CUA
        tache_cua = {
            "tache_1": {
                "id": "tache_1",
                "description": requete,
                "type": "cua_complex",
                "dependances": []
            }
        }
        
        graphe = {
            "taches": tache_cua,
            "ordre_execution": ["tache_1"]
        }
        
        # Exécuter avec CUA
        resultats = self.executer_avec_reprise(graphe)
        
        # Sauvegarder sans skills (CUA apprend visuellement)
        self.memory.sauvegarder_interaction(requete, {
            "type": "cua_complex",
            "resultats": resultats,
            "timestamp": datetime.now().isoformat()
        })
        
        # Générer réponse
        if resultats.get("tache_1", {}).get("status") == "success":
            return f"Tâche accomplie avec succès ! {resultats['tache_1'].get('resultat', '')}"
        else:
            return "Je n'ai pas pu accomplir complètement la tâche."
    def traiter_action_simple(self, requete, intention):
        """Traite une action simple directement sans planification"""
        print(f"🎯 Exécution action simple: {requete}")
        
        # Créer une tâche unique simple
        tache_simple = {
            "tache_1": {
                "id": "tache_1",
                "description": requete,
                "type": "action_simple",
                "dependances": []
            }
        }
        
        graphe = {
            "taches": tache_simple,
            "ordre_execution": ["tache_1"]
        }
        
        # Exécuter directement
        resultats = self.executer_avec_reprise(graphe)
        
        # Sauvegarder (sans créer de skills)
        self.memory.sauvegarder_interaction(requete, {
            "type": "action_simple",
            "resultats": resultats,
            "timestamp": datetime.now().isoformat()
        })
        
        # Réponse simple
        if resultats.get("tache_1", {}).get("status") == "success":
            return resultats["tache_1"].get("resultat", "✅ Action exécutée")
        else:
            return "❌ L'action a échoué"
    
    def executer_avec_reprise(self, graphe_taches):
        resultats = {}
        taches_ignorees = []
        
        for tache_id in graphe_taches["ordre_execution"]:
            tache = graphe_taches["taches"][tache_id]
            
            if self.dependances_satisfaites(tache, resultats):
                execution_result = self.executeur.executer_tache_avec_verification(tache)
                
                # 🔥 TOUJOURS STOCKER LE DICT COMPLET
                resultats[tache_id] = execution_result
                
                if execution_result["status"] == "success":
                    print(f"✅ {tache['description']} - TERMINÉ")
                elif execution_result["status"] == "user_intervention_failed":
                    print(f"⏭️ {tache['description']} - IGNORÉ")
                    taches_ignorees.append(tache_id)
                elif execution_result["status"] == "failed":
                    print(f"💥 {tache['description']} - ÉCHEC")
                    if self.interface_utilisateur.demander_confirmation("Continuer sans cette tâche?"):
                        taches_ignorees.append(tache_id)
                    else:
                        break
        
        if taches_ignorees:
            self.verifier_impact_taches_ignorees(taches_ignorees, graphe_taches, resultats)
        
        return resultats
    
    def dependances_satisfaites(self, tache, resultats_existants):
        for dependance in tache.get("dependances", []):
            if dependance not in resultats_existants:
                return False
        return True
    
    def verifier_impact_taches_ignorees(self, taches_ignorees, graphe_taches, resultats):
        for tache_id in graphe_taches["ordre_execution"]:
            if tache_id not in taches_ignorees and tache_id not in resultats:
                tache = graphe_taches["taches"][tache_id]
                for dependance in tache.get("dependances", []):
                    if dependance in taches_ignorees:
                        print(f"⚠️  '{tache['description']}' dépend de '{dependance}' ignorée")
    
    def apprendre_et_memoriser(self, graphe_taches, resultats, requete_utilisateur):
        skills_ajoutes = []
        
        for tache_id, execution_data in resultats.items():
            # 🔥 MAINTENANT execution_data EST TOUJOURS UN DICT
            if execution_data["status"] == "success":
                tache = graphe_taches["taches"][tache_id]
                resultat = execution_data["resultat"]
                commande_utilisee = execution_data["commande_utilisee"]
                
                # Ne pas créer de skills pour les tâches CUA (elles apprennent visuellement)
                if tache.get('type') == 'cua_complex':
                    print("🤖 Tâche CUA - Pas de skill créé (apprentissage visuel)")
                    continue
                
                if self.verificateur.verifier(tache, resultat):
                    description = tache['description']
                    
                    if commande_utilisee and self.skill_manager.evaluer_reutilisabilite(description, resultat):
                        self.skill_manager.ajouter_skill(description, commande_utilisee)
                        skills_ajoutes.append(description)
                        print(f"💡 Skill créé: {description}")
        
        # Sauvegarde mémoire
        self.memory.sauvegarder_interaction(requete_utilisateur, {
            "resultats": {k: v["resultat"] for k, v in resultats.items() if v["status"] == "success"},
            "skills_ajoutes": skills_ajoutes,
            "timestamp": datetime.now().isoformat()
        })
        
        if skills_ajoutes:
            print(f"🎯 Skills ajoutés: {', '.join(skills_ajoutes)}")
    
    def generer_reponse_contextuelle(self, requete, resultats):
        historique = self.memory.get_contexte_recent(requete)
        
        # Compter les succès
        succes = sum(1 for r in resultats.values() if r["status"] == "success")
        total = len(resultats)
        
        prompt = f"""
        Historique: {historique}
        
        L'utilisateur a demandé: "{requete}"
        Résultat: {succes}/{total} tâches accomplies avec succès.
        
        Génère une réponse naturelle qui résume ce qui a été fait.
        Mentionne les nouveaux skills appris si pertinent.
        """
        
        return self.ollama_client.generate(prompt)