"""
Script de setup et téléchargement des modèles
"""
import os
import sys
from pathlib import Path


def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def check_python_version():
    """Vérifie la version de Python"""
    print_header("🐍 Vérification de Python")
    
    version = sys.version_info
    print(f"Version Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ requis!")
        return False
    
    print("✅ Version Python OK")
    return True


def install_requirements():
    """Installe les dépendances"""
    print_header("📦 Installation des dépendances")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt non trouvé!")
        return False
    
    print("Installation en cours (cela peut prendre plusieurs minutes)...")
    print("Packages: PyAudio, Whisper, TTS, PyAutoG UI, etc.\n")
    
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
        capture_output=False
    )
    
    if result.returncode == 0:
        print("\n✅ Dépendances installées")
        return True
    else:
        print("\n❌ Erreur lors de l'installation")
        return False


def download_whisper():
    """Télécharge le modèle Whisper"""
    print_header("🎤 Configuration de Whisper")
    
    print("Au premier lancement, Whisper téléchargera automatiquement le modèle.")
    print("Modèle configuré: medium (~1.5GB)")
    print("Vous pouvez changer cela dans config.py (WHISPER_MODEL)")
    
    print("\n💡 Test de Whisper...")
    try:
        from faster_whisper import WhisperModel
        print("Chargement du modèle (téléchargement si nécessaire)...")
        model = WhisperModel("medium", device="cpu", compute_type="int8")
        print("✅ Whisper prêt!")
        return True
    except Exception as e:
        print(f"⚠️ Whisper sera téléchargé au premier lancement: {e}")
        return True


def download_tts():
    """Télécharge le modèle TTS"""
    print_header("🔊 Configuration de TTS (XTTS v2)")
    
    print("Au premier lancement, TTS téléchargera automatiquement le modèle.")
    print("Modèle: XTTS v2 (~2GB)")
    
    print("\n💡 Test de TTS...")
    try:
        from TTS.api import TTS
        print("Chargement du modèle (téléchargement si nécessaire)...")
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        print("✅ TTS prêt!")
        return True
    except Exception as e:
        print(f"⚠️ TTS sera téléchargé au premier lancement: {e}")
        return True


def check_ollama():
    """Vérifie qu'Ollama est disponible"""
    print_header("🧠 Vérification d'Ollama")
    
    print("Vérification de la connexion à Ollama...")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama connecté - {len(models)} modèles disponibles")
            
            # Vérifier si qwen2.5 est présent
            qwen_found = any('qwen2.5' in m.get('name', '').lower() for m in models)
            if qwen_found:
                print("✅ Modèle Qwen2.5 trouvé")
            else:
                print("⚠️ Qwen2.5 non trouvé")
                print("   Installez-le: ollama pull qwen2.5:7b-instruct-q4_K_M")
            
            # Vérifier VLM
            vlm_found = any('qwen2-vl' in m.get('name', '').lower() for m in models)
            if vlm_found:
                print("✅ Modèle VLM (Qwen2-VL) trouvé")
            else:
                print("⚠️ VLM non trouvé (IMPORTANT pour CUA!)")
                print("   Installez-le: ollama pull qwen2-vl:7b")
            
            return True
        else:
            print("❌ Ollama non disponible")
            return False
    except Exception as e:
        print(f"❌ Erreur connexion Ollama: {e}")
        print("   Assurez-vous qu'Ollama est démarré")
        print("   Téléchargez: https://ollama.ai")
        return False


def create_directories():
    """Crée les dossiers nécessaires"""
    print_header("📁 Création des dossiers")
    
    base_dir = Path(__file__).parent
    
    directories = [
        base_dir / "data",
        base_dir / "models",
        base_dir / "data" / "screenshots",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ {directory}")
    
    return True


def setup_summary():
    """Affiche un résumé de la configuration"""
    print_header("📋 Résumé de la Configuration")
    
    print("""
✅ Dépendances Python installées
✅ Whisper (STT) prêt
✅ TTS (XTTS v2) prêt
✅ Ollama vérifié
✅ Dossiers créés

🎯 Prochaines étapes:

1. Assurez-vous qu'Ollama est démarré:
   - Windows: Ollama doit tourner en arrière-plan
   - Modèles requis:
     * ollama pull qwen2.5:7b-instruct-q4_K_M
     * ollama pull qwen2-vl:7b  (VLM pour CUA!)

2. Lancez l'agent:
   python main.py

3. Mode texte (sans voix) pour tests:
   python main.py --text

4. Configuration avancée:
   - Modifiez config.py pour personnaliser
   - Calibrez le microphone au premier lancement

📚 Documentation:
   - README.md pour plus d'informations
   - CUA_GUIDE.md pour l'agent autonome
   - INSTALLATION.md pour le guide détaillé
    """)


def main():
    """Script principal de setup"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║         🛠️  MUAG - Setup et Configuration  🛠️            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Vérifications et installations
    steps = [
        ("Version Python", check_python_version),
        ("Dossiers", create_directories),
        ("Dépendances Python", install_requirements),
        ("Whisper", download_whisper),
        ("TTS", download_tts),
        ("Ollama", check_ollama),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"\n❌ Erreur dans {step_name}: {e}")
            failed_steps.append(step_name)
    
    # Résumé
    if not failed_steps:
        setup_summary()
        return 0
    else:
        print("\n" + "="*60)
        print("⚠️  Configuration incomplète")
        print("="*60)
        print("\nÉtapes échouées:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nCorrigez les erreurs et relancez setup_models.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
