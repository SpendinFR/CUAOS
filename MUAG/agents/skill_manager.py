import json
import os
from datetime import datetime
from config import SKILLS_FILE
from utils.ollama_client import OllamaClient

class SkillManager:
    def __init__(self):
        self.client = OllamaClient()
        self.skills_file = SKILLS_FILE
        self.skills = self.charger_skills()
        print(f"📚 {len(self.skills)} skills chargés")
    
    def charger_skills(self):
        try:
            if os.path.exists(self.skills_file):
                with open(self.skills_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ Erreur chargement skills: {e}")
        return []
    
    def sauvegarder_skills(self):
        try:
            with open(self.skills_file, 'w', encoding='utf-8') as f:
                json.dump(self.skills, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Erreur sauvegarde skills: {e}")
    
    def trouver_skill(self, description):
        for skill in self.skills:
            similarite = self.calculer_similarite_amelioree(skill["description"], description)
            if similarite > 0.7:
                print(f"🔍 Similarité {similarite:.2f} entre '{skill['description']}' et '{description}'")
                return skill
        return None
    
    def calculer_similarite_amelioree(self, texte1, texte2):
        """🔥 NOUVELLE MÉTHODE PLUS INTELLIGENTE"""
        texte1_lower = texte1.lower()
        texte2_lower = texte2.lower()
        
        # 🔥 MOTS-CLÉS SPÉCIFIQUES (prennent plus de poids)
        mots_specifiques = ["chrome", "spotify", "facebook", "google", "youtube", "notepad", "calculator", "epic", "fortnite"]
        # 🔥 MOTS GÉNÉRIQUES (prennent moins de poids)
        mots_generiques = ["ouvrir", "lancer", "start", "aller", "chercher", "va", "sur"]
        
        # Score basé sur les mots spécifiques
        score_specifique = 0
        for mot in mots_specifiques:
            if mot in texte1_lower and mot in texte2_lower:
                score_specifique += 0.4  # 🔥 Forte pénalité si les mots spécifiques diffèrent
            elif mot in texte1_lower or mot in texte2_lower:
                score_specifique -= 0.2  # 🔥 Un seul a le mot spécifique = probablement différent
        
        # Score basé sur les mots génériques
        score_generique = 0
        mots_communs_generiques = 0
        for mot in mots_generiques:
            if mot in texte1_lower and mot in texte2_lower:
                mots_communs_generiques += 1
        
        score_generique = mots_communs_generiques * 0.1  # 🔥 Faible poids pour les génériques
        
        # Similarité de base par mots communs
        mots1 = set(texte1_lower.split())
        mots2 = set(texte2_lower.split())
        intersection = mots1.intersection(mots2)
        union = mots1.union(mots2)
        similarite_base = len(intersection) / len(union) if union else 0
        
        # 🔥 COMBINAISON FINALE
        similarite_totale = similarite_base + score_generique + score_specifique
        
        # Limiter entre 0 et 1
        return max(0, min(1, similarite_totale))
    
    def evaluer_reutilisabilite(self, description, resultat):
        # 🔥 RÈGLES PLUS PRÉCISES
        description_lower = description.lower()
        
        # Actions toujours réutilisables
        if any(mot in description_lower for mot in ["lancer", "ouvrir", "start"]):
            return True
        
        # Actions conditionnellement réutilisables
        if any(mot in description_lower for mot in ["aller sur", "chercher", "rechercher"]):
            # Vérifier que c'est un site web connu
            sites_web = ["google", "facebook", "youtube", "twitter", "github"]
            if any(site in description_lower for site in sites_web):
                return True
        
        # Vérifier le succès
        resultat_str = str(resultat).lower()
        if "erreur" in resultat_str or "n'est pas reconnu" in resultat_str:
            return False
        
        # Fallback LLM pour les cas ambigus
        prompt = f"""
        La tâche "{description}" est-elle réutilisable dans d'autres contextes?
        Exemple: "Ouvrir Chrome" = OUI, "Chercher python" = OUI, "Acheter des chaussures" = NON
        Réponds uniquement par OUI ou NON.
        """
        return self.client.generate(prompt).strip().upper() == "OUI"
    
    def ajouter_skill(self, description, commande):
        # Nettoyer la commande
        commande_clean = commande.strip()
        
        # 🔥 VÉRIFICATION PLUS STRICTE DES DOUBLONS
        similarite_existante = 0
        skill_existant = None
        
        for skill in self.skills:
            similarite = self.calculer_similarite_amelioree(skill["description"], description)
            if similarite > similarite_existante:
                similarite_existante = similarite
                skill_existant = skill
        
        if similarite_existante > 0.8:
            print(f"🔁 Skill similaire existe déjà ({similarite_existante:.2f}): '{skill_existant['description']}'")
            skill_existant["usage_count"] += 1
            self.sauvegarder_skills()
            return
        
        # Nouveau skill
        nouveau_skill = {
            "description": description,
            "commande": commande_clean,
            "usage_count": 1,
            "date_creation": datetime.now().isoformat()
        }
        
        self.skills.append(nouveau_skill)
        self.sauvegarder_skills()
        print(f"💾 NOUVEAU Skill: '{description}' → '{commande_clean}'")