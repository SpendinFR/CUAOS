"""
Script de test pour l'agent CUA autonome
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actions.cua_agent import CUAAgent


def test_simple_task():
    """Test simple: ouvrir le bloc-notes"""
    print("\n" + "="*60)
    print("TEST 1: Tâche simple - Ouvrir le bloc-notes")
    print("="*60 + "\n")
    
    agent = CUAAgent()
    result = agent.execute_task("Ouvre le bloc-notes", max_steps=5)
    
    print(agent.get_summary())
    print(f"\nRésultat: {result['status']}")
    print(f"Terminé: {result['completed']}")


def test_web_search():
    """Test web: chercher sur Google"""
    print("\n" + "="*60)
    print("TEST 2: Recherche web - Google")
    print("="*60 + "\n")
    
    agent = CUAAgent()
    result = agent.execute_task("Cherche la météo à Paris sur Google", max_steps=10)
    
    print(agent.get_summary())
    print(f"\nRésultat: {result['status']}")
    print(f"Terminé: {result['completed']}")


def test_complex_task():
    """Test complexe: navigation et interaction"""
    print("\n" + "="*60)
    print("TEST 3: Tâche complexe - Navigation Amazon (SIMULATION)")
    print("="*60 + "\n")
    
    agent = CUAAgent()
    result = agent.execute_task(
        "Va sur amazon.fr et cherche des écouteurs sans fil",
        max_steps=15
    )
    
    print(agent.get_summary())
    print(f"\nRésultat: {result['status']}")
    print(f"Terminé: {result['completed']}")


def test_custom_task(task_description):
    """Test personnalisé"""
    print("\n" + "="*60)
    print(f"TEST PERSONNALISÉ: {task_description}")
    print("="*60 + "\n")
    
    agent = CUAAgent()
    result = agent.execute_task(task_description, max_steps=20)
    
    print(agent.get_summary())
    print(f"\nRésultat: {result['status']}")
    print(f"Terminé: {result['completed']}")


def main():
    """Menu de test"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      🤖  Test Agent CUA Autonome - MUAG  🤖             ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  IMPORTANT:")
    print("- Assurez-vous qu'Ollama est démarré")
    print("- Un modèle VLM est recommandé: ollama pull qwen2-vl:7b")
    print("- Sans VLM, l'agent fonctionnera en mode limité\n")
    
    if len(sys.argv) > 1:
        # Mode CLI avec tâche en argument
        task = " ".join(sys.argv[1:])
        test_custom_task(task)
    else:
        # Menu interactif
        while True:
            print("\n" + "="*60)
            print("MENU DE TEST")
            print("="*60)
            print("1. Test simple (ouvrir bloc-notes)")
            print("2. Test web (recherche Google)")
            print("3. Test complexe (simulation Amazon)")
            print("4. Tâche personnalisée")
            print("5. Quitter")
            print("="*60)
            
            choix = input("\nChoix: ").strip()
            
            if choix == "1":
                test_simple_task()
            elif choix == "2":
                test_web_search()
            elif choix == "3":
                test_complex_task()
            elif choix == "4":
                task = input("\nDécrivez la tâche: ").strip()
                if task:
                    test_custom_task(task)
            elif choix == "5":
                print("\n👋 Au revoir!\n")
                break
            else:
                print("❌ Choix invalide")
            
            input("\nAppuyez sur Entrée pour continuer...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interruption détectée\n")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
