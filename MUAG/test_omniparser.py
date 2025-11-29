"""
Test OmniParser Integration
Teste la détection UI + caption sémantique avec OmniParser
"""
import cv2
import numpy as np
from pathlib import Path
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from actions.omniparser_detector import omniparser


def test_omniparser():
    """Test basique d'OmniParser"""
    
    print("=" * 60)
    print("TEST OMNIPARSER - UI Detection + Semantic Caption")
    print("=" * 60)
    
    # Créer une image de test simple (ou utiliser une vraie capture)
    test_image_path = Path("data/screenshots")
    
    if not test_image_path.exists():
        print("\n⚠️ Aucun screenshot trouvé dans data/screenshots")
        print("Création d'une image de test...")
        
        # Créer une image de test simple
        img = np.ones((800, 1200, 3), dtype=np.uint8) * 255
        
        # Dessiner quelques "boutons" simulés
        cv2.rectangle(img, (100, 100), (300, 150), (200, 200, 200), -1)
        cv2.putText(img, "Search", (150, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        cv2.rectangle(img, (350, 100), (450, 150), (200, 200, 200), -1)
        cv2.putText(img, "X", (390, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        test_path = Path("test_screenshot.png")
        cv2.imwrite(str(test_path), img)
        print(f"✅ Image de test créée: {test_path}")
    else:
        # Utiliser le screenshot le plus récent
        screenshots = list(test_image_path.glob("*.png"))
        if screenshots:
            test_path = sorted(screenshots, key=lambda p: p.stat().st_mtime)[-1]
            print(f"📸 Utilisation du screenshot: {test_path}")
            img = cv2.imread(str(test_path))
        else:
            print("❌ Aucun screenshot trouvé")
            return False
    
    # Test de détection
    print("\n🔮 Lancement détection OmniParser...")
    print("-" * 60)
    
    try:
        detections = omniparser.detect_ui_elements(img)
        
        print("\n" + "=" * 60)
        print(f"✅ RÉSULTATS: {len(detections)} éléments détectés")
        print("=" * 60)
        
        if detections:
            print("\n📋 DÉTAILS DES DÉTECTIONS:\n")
            for det in detections[:10]:  # Afficher max 10
                print(f"  ID {det['id']}: {det['description']}")
                print(f"      Position: {det['center']} | Bbox: {det['bbox']}")
                print(f"      Confiance: {det['confidence']:.2f}")
                print()
            
            if len(detections) > 10:
                print(f"  ... et {len(detections) - 10} autres éléments\n")
            
            # Test du format LLM
            print("\n" + "=" * 60)
            print("FORMAT POUR VLM #2:")
            print("=" * 60)
            formatted = omniparser.format_for_llm(detections)
            print(formatted)
            
            print("\n" + "=" * 60)
            print("✅ TEST RÉUSSI!")
            print("=" * 60)
            return True
        else:
            print("\n⚠️ Aucun élément détecté")
            print("Vérifiez que OmniParser est correctement installé (/install_omniparser)")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Solution:")
        print("   1. Exécutez /install_omniparser pour installer OmniParser")
        print("   2. Vérifiez que les modèles sont téléchargés dans OmniParser/weights/")
        return False


if __name__ == "__main__":
    success = test_omniparser()
    sys.exit(0 if success else 1)
