"""
TTS Engine - Text-to-Speech utilisant XTTS v2 Coqui
"""
import torch
import numpy as np
from TTS.api import TTS
import soundfile as sf
from pathlib import Path
import tempfile

from config import (
    TTS_MODEL,
    TTS_DEVICE,
    TTS_LANGUAGE,
    TTS_SPEAKER_WAV,
    AUDIO_SAMPLE_RATE
)


class TTSEngine:
    def __init__(self, model_name=None, device=None, speaker_wav=None):
        """
        Initialise le moteur TTS avec XTTS v2
        Args:
            model_name: nom du modèle TTS
            device: auto, cpu, cuda
            speaker_wav: chemin vers un fichier audio pour cloner la voix (optionnel)
        """
        self.model_name = model_name or TTS_MODEL
        self.device = device or TTS_DEVICE
        self.language = TTS_LANGUAGE
        self.speaker_wav = speaker_wav or TTS_SPEAKER_WAV
        
        print(f"🔄 Chargement du modèle TTS ({self.model_name})...")
        
        try:
            # Déterminer le device
            if self.device == "auto":
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Charger le modèle
            self.tts = TTS(self.model_name).to(self.device)
            
            print(f"✅ TTS chargé sur {self.device}")
            
            # Si XTTS, vérifier les speakers disponibles
            if "xtts" in self.model_name.lower():
                self.is_multi_speaker = True
                print("🎤 Mode multi-speaker activé (XTTS)")
            else:
                self.is_multi_speaker = False
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement de TTS: {e}")
            raise
    
    def synthesize(self, text, language=None, speaker_wav=None, save_path=None):
        """
        Synthétise le texte en audio
        Args:
            text: texte à synthétiser
            language: code langue (fr, en, etc.)
            speaker_wav: fichier audio pour cloner la voix (pour XTTS)
            save_path: chemin pour sauvegarder (optionnel)
        Returns:
            numpy array: données audio
        """
        if not text or text.strip() == "":
            print("⚠️ Texte vide, pas de synthèse")
            return None
        
        try:
            language = language or self.language
            speaker_wav = speaker_wav or self.speaker_wav
            
            print(f"🔊 Synthèse: '{text[:50]}...'")
            
            if self.is_multi_speaker and speaker_wav:
                # XTTS avec clonage de voix
                wav = self.tts.tts(
                    text=text,
                    language=language,
                    speaker_wav=speaker_wav
                )
            elif self.is_multi_speaker:
                # XTTS sans clonage (voix par défaut)
                # Pour XTTS, on doit fournir un speaker_wav ou utiliser un speaker prédéfini
                # On va créer une voix neutre par défaut
                wav = self.tts.tts(
                    text=text,
                    language=language
                )
            else:
                # Modèle simple sans multi-speaker
                wav = self.tts.tts(text=text)
            
            # Convertir en numpy array
            wav = np.array(wav)
            
            # Sauvegarder si demandé
            if save_path:
                sf.write(save_path, wav, self.tts.synthesizer.output_sample_rate)
                print(f"💾 Audio sauvegardé: {save_path}")
            
            return wav
            
        except Exception as e:
            print(f"❌ Erreur lors de la synthèse: {e}")
            return None
    
    def synthesize_to_file(self, text, output_file, language=None, speaker_wav=None):
        """
        Synthétise le texte et sauvegarde directement dans un fichier
        """
        try:
            language = language or self.language
            speaker_wav = speaker_wav or self.speaker_wav
            
            if self.is_multi_speaker and speaker_wav:
                self.tts.tts_to_file(
                    text=text,
                    language=language,
                    speaker_wav=speaker_wav,
                    file_path=output_file
                )
            elif self.is_multi_speaker:
                self.tts.tts_to_file(
                    text=text,
                    language=language,
                    file_path=output_file
                )
            else:
                self.tts.tts_to_file(
                    text=text,
                    file_path=output_file
                )
            
            print(f"✅ Audio synthétisé: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la synthèse: {e}")
            return False
    
    def get_sample_rate(self):
        """Retourne le sample rate du modèle"""
        if hasattr(self.tts, 'synthesizer') and hasattr(self.tts.synthesizer, 'output_sample_rate'):
            return self.tts.synthesizer.output_sample_rate
        return 22050  # Valeur par défaut
    
    def list_available_models(self):
        """Liste tous les modèles TTS disponibles"""
        return TTS.list_models()
    
    def get_model_info(self):
        """Retourne les informations sur le modèle"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "language": self.language,
            "is_multi_speaker": self.is_multi_speaker,
            "speaker_wav": self.speaker_wav,
            "sample_rate": self.get_sample_rate()
        }
    
    def set_speaker_wav(self, speaker_wav_path):
        """Définit un nouveau fichier de référence pour le clonage de voix"""
        if Path(speaker_wav_path).exists():
            self.speaker_wav = speaker_wav_path
            print(f"🎤 Voix de référence mise à jour: {speaker_wav_path}")
            return True
        else:
            print(f"❌ Fichier non trouvé: {speaker_wav_path}")
            return False
