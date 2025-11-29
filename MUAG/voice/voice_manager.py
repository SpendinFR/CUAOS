"""
Voice Manager - Orchestrateur de l'interface vocale
Gère la boucle STT → Agent → TTS
"""
from .stt_engine import STTEngine
from .tts_engine import TTSEngine
from .audio_handler import AudioHandler
import numpy as np
from pathlib import Path


class VoiceManager:
    def __init__(self):
        """Initialise le gestionnaire vocal"""
        print("🎙️ Initialisation du gestionnaire vocal...")
        
        # Initialiser les composants
        self.audio_handler = AudioHandler()
        self.stt_engine = None
        self.tts_engine = None
        
        self.is_initialized = False
        self.is_listening = False
    
    def initialize(self, calibrate_mic=True):
        """
        Initialise les moteurs STT et TTS
        Args:
            calibrate_mic: calibrer le microphone au démarrage
        """
        try:
            # Charger STT
            print("\n📥 Chargement de Whisper...")
            self.stt_engine = STTEngine()
            
            # Charger TTS
            print("\n📥 Chargement de XTTS...")
            self.tts_engine = TTSEngine()
            
            # Calibrer le microphone si demandé
            if calibrate_mic:
                print("\n🎚️ Calibration du microphone...")
                self.audio_handler.calibrate_silence_threshold(duration=3)
            
            self.is_initialized = True
            print("\n✅ Gestionnaire vocal prêt!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erreur lors de l'initialisation: {e}")
            return False
    
    def listen(self):
        """
        Écoute l'utilisateur et transcrit en texte
        Returns:
            str: texte transcrit ou None
        """
        if not self.is_initialized:
            print("❌ Gestionnaire vocal non initialisé")
            return None
        
        try:
            # Enregistrer l'audio
            audio_data = self.audio_handler.record_until_silence()
            
            if audio_data is None:
                return None
            
            # Transcrire
            print("🔄 Transcription en cours...")
            text = self.stt_engine.transcribe(audio_data)
            
            if text:
                print(f"📝 Transcrit: {text}")
                return text
            else:
                print("⚠️ Aucun texte détecté")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de l'écoute: {e}")
            return None
    
    def speak(self, text, save_path=None):
        """
        Synthétise et joue le texte
        Args:
            text: texte à dire
            save_path: optionnel, chemin pour sauvegarder l'audio
        """
        if not self.is_initialized:
            print("❌ Gestionnaire vocal non initialisé")
            return False
        
        if not text or text.strip() == "":
            return False
        
        try:
            # Synthétiser
            audio_wav = self.tts_engine.synthesize(text, save_path=save_path)
            
            if audio_wav is None:
                return False
            
            # Jouer l'audio
            sample_rate = self.tts_engine.get_sample_rate()
            
            # Convertir en int16 pour PyAudio
            audio_int16 = (audio_wav * 32767).astype(np.int16)
            
            print("🔊 Lecture audio...")
            self.audio_handler.play_audio(audio_int16, sample_rate=sample_rate)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la synthèse/lecture: {e}")
            return False
    
    def conversation_loop(self, callback):
        """
        Boucle de conversation continue
        Args:
            callback: fonction(user_text) -> agent_response
        """
        print("\n🎯 Mode conversation activé")
        print("   Dites 'stop' ou 'arrête' pour quitter")
        print("   Dites 'pause' pour mettre en pause\n")
        
        self.is_listening = True
        paused = False
        
        while self.is_listening:
            try:
                if paused:
                    print("⏸️  En pause - dites 'continue' pour reprendre")
                    user_text = self.listen()
                    if user_text and any(word in user_text.lower() for word in ['continue', 'reprends', 'reprise']):
                        paused = False
                        self.speak("Je reprends l'écoute")
                    continue
                
                # Écouter l'utilisateur
                user_text = self.listen()
                
                if not user_text:
                    continue
                
                # Commandes système
                lower_text = user_text.lower()
                
                if any(word in lower_text for word in ['stop', 'arrête', 'arrêter', 'au revoir']):
                    self.speak("Au revoir!")
                    self.is_listening = False
                    break
                
                if any(word in lower_text for word in ['pause', 'attends']):
                    paused = True
                    self.speak("Je me mets en pause")
                    continue
                
                # Traiter la requête via le callback
                print(f"\n💭 Traitement: {user_text}")
                agent_response = callback(user_text)
                
                # Répondre
                if agent_response:
                    print(f"🤖 Réponse: {agent_response}")
                    self.speak(agent_response)
                
            except KeyboardInterrupt:
                print("\n\n⚠️ Interruption détectée")
                self.is_listening = False
                break
            except Exception as e:
                print(f"\n❌ Erreur dans la boucle: {e}")
                self.speak("Désolé, j'ai rencontré une erreur")
        
        print("\n👋 Fin de la conversation")
    
    def test_voice(self):
        """Test rapide du système vocal"""
        print("\n🧪 Test du système vocal\n")
        
        # Test TTS
        print("1️⃣ Test TTS...")
        self.speak("Bonjour, je suis votre assistant vocal.")
        
        # Test STT
        print("\n2️⃣ Test STT...")
        print("   Dites quelque chose...")
        text = self.listen()
        
        if text:
            print(f"\n✅ Test réussi! Vous avez dit: {text}")
            self.speak(f"Vous avez dit: {text}")
        else:
            print("\n❌ Test échoué")
        
    def cleanup(self):
        """Libère les ressources"""
        print("🧹 Nettoyage des ressources...")
        if self.audio_handler:
            self.audio_handler.cleanup()
        print("✅ Ressources libérées")
