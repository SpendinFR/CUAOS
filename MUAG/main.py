# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
MUAG - Multi-modal Autonomous Agent
Agent vocal autonome avec capacites d'interaction et d'actions
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice import VoiceManager
from agents.coordinateur import Coordinateur
from config import AGENT_NAME
import traceback


def banner():
    """Affiche le banner de demarrage"""
    print("""
============================================================
                                                          
      MUAG - Agent Vocal Autonome Local                  
                                                          
  [Micro] Interface Vocale (STT/TTS)                          
  [Brain] LLM Local (Ollama Qwen2.5)                          
  [Target] Decision Intelligente (Repondre/Agir)               
  [PC] Actions Completes sur l'Ordinateur                  
                                                          
============================================================
    """)


def main():
    """Point d'entree principal avec interface vocale"""
    banner()
    
    try:
        print("\\n[*] Initialisation du systeme...\\n")
        
        # Initialiser le gestionnaire vocal
        voice_manager = VoiceManager()
        
        print("[*] Chargement des modeles (cela peut prendre un moment)...")
        if not voice_manager.initialize(calibrate_mic=True):
            print("\\n[ERROR] Echec de l'initialisation")
            print("   Verifiez que les modeles sont installes:")
            print("   - Whisper: faster-whisper")
            print("   - TTS: Coqui TTS")
            return 1
        
        # Initialiser le coordinateur
        coordinateur = Coordinateur()
        
        # Test optionnel du systeme
        test_voice = input("\\n[?] Tester le systeme vocal avant de commencer? (o/n): ").strip().lower()
        if test_voice in ['o', 'oui', 'y', 'yes']:
            voice_manager.test_voice()
        
        print("\\n" + "="*60)
        print("[OK] Systeme pret!")
        print("="*60)
        print(f"\\n[Micro] Je suis {AGENT_NAME}, votre assistant vocal autonome.")
        print("\\n[i] Commandes vocales disponibles:")
        print("   - 'stop' / 'arrete' : Quitter")
        print("   - 'pause' : Mettre en pause")
        print("   - 'continue' : Reprendre apres une pause")
        print("\\n[Exemples] Requetes:")
        print("   [Chat] Conversation: 'Bonjour', 'Comment ca va?', 'Raconte une blague'")
        print("   [App] Actions simples: 'Ouvre Chrome', 'Lance la calculatrice'")
        print("   [Web] Actions web: 'Cherche la meteo a Paris sur Google'")
        print("   [File] Fichiers: 'Cree un fichier test.txt sur le bureau'")
        print("   [Mem] Memoire: 'Quel est mon film prefere?' (apres l'avoir dit)")
        print("\\n" + "="*60 + "\\n")
        
        # Dire bonjour
        voice_manager.speak(f"Bonjour! Je suis {AGENT_NAME}. Comment puis-je vous aider aujourd'hui?")
        
        def traiter_requete(user_text):
            """Callback pour traiter chaque requete utilisateur"""
            try:
                # Le coordinateur decide: conversation vs action
                reponse = coordinateur.traiter_requete(user_text)
                return reponse
            except Exception as e:
                print(f"\\n[ERROR] Erreur lors du traitement: {e}")
                traceback.print_exc()
                return "Desole, j'ai rencontre une erreur en traitant votre demande."
        
        # Lancer la boucle de conversation
        voice_manager.conversation_loop(traiter_requete)
        
    except KeyboardInterrupt:
        print("\\n\\n[!] Interruption detectee")
    except Exception as e:
        print(f"\\n[ERROR] Erreur fatale: {e}")
        traceback.print_exc()
        return 1
    finally:
        # Nettoyage
        print("\n[*] Nettoyage...")
        
        # ✅ AJOUTER ICI
        try:
            coordinateur.executeur.shutdown()
        except Exception as e:
            print(f"[Warning] Erreur shutdown: {e}")
        
        try:
            voice_manager.cleanup()
        except:
            pass
        
        print("[Bye] Au revoir!\n")
    return 0


def mode_texte():
    """Mode texte (sans voix) pour tests"""
    banner()
    print("\\n[Text Mode] Mode Texte (sans voix)\\n")
    
    coordinateur = Coordinateur()
    
    print("[i] Tapez 'quit' pour quitter\\n")
    
    while True:
        try:
            requete = input("\\n[You] Vous: ").strip()
            
            if not requete:
                continue
            
            if requete.lower() in ['quit', 'exit', 'q']:
                break
            
            print("\\n[AI] Traitement...\\n")
            reponse = coordinateur.traiter_requete(requete)
            print(f"\\n[{AGENT_NAME}] {AGENT_NAME}: {reponse}\\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\\n[ERROR] Erreur: {e}")
            traceback.print_exc()
            
    # Consolidation session avant de quitter
    try:
        coordinateur.executeur.shutdown()
    except Exception as e:
        print(f"\n[Warning] Erreur shutdown: {e}")
    
    print("\\n[Bye] Au revoir!\\n")


if __name__ == "__main__":
    # Verifier si mode texte demande
    if len(sys.argv) > 1 and sys.argv[1] == "--text":
        mode_texte()
    else:
        sys.exit(main())