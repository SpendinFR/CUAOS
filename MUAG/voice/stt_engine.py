"""
STT Engine - Speech-to-Text utilisant Whisper local (faster-whisper)
"""
import numpy as np
from faster_whisper import WhisperModel
import warnings
warnings.filterwarnings("ignore")

from config import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_LANGUAGE,
    WHISPER_VAD_FILTER,
    AUDIO_SAMPLE_RATE
)


class STTEngine:
    def __init__(self, model_size=None, device=None, compute_type=None):
        """
        Initialise le moteur STT avec Whisper
        Args:
            model_size: tiny, base, small, medium, large-v2, large-v3
            device: auto, cpu, cuda
            compute_type: int8, float16, float32
        """
        self.model_size = model_size or WHISPER_MODEL
        self.device = device or WHISPER_DEVICE
        self.compute_type = compute_type or WHISPER_COMPUTE_TYPE
        self.language = WHISPER_LANGUAGE
        self.vad_filter = WHISPER_VAD_FILTER
        
        print(f"🔄 Chargement du modèle Whisper ({self.model_size})...")
        
        try:
            # Déterminer le device
            if self.device == "auto":
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            print(f"✅ Whisper chargé sur {self.device}")
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement de Whisper: {e}")
            raise
    
    def transcribe(self, audio_data, language=None):
        """
        Transcrit l'audio en texte
        Args:
            audio_data: bytes or numpy array
            language: code langue (fr, en, etc.) ou None pour auto-détection
        Returns:
            str: texte transcrit
        """
        try:
            # Convertir bytes en numpy array si nécessaire
            if isinstance(audio_data, bytes):
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_np = audio_data.astype(np.float32) / 32768.0
            
            # Transcription
            segments, info = self.model.transcribe(
                audio_np,
                language=language or self.language,
                vad_filter=self.vad_filter,
                beam_size=5
            )
            
            # Assembler les segments
            text = " ".join([segment.text for segment in segments]).strip()
            
            # Info de détection de langue
            if not language:
                print(f"🌍 Langue détectée: {info.language} (probabilité: {info.language_probability:.2f})")
            
            return text
            
        except Exception as e:
            print(f"❌ Erreur lors de la transcription: {e}")
            return ""
    
    def transcribe_file(self, audio_file, language=None):
        """
        Transcrit un fichier audio
        Args:
            audio_file: chemin vers le fichier audio
            language: code langue ou None
        Returns:
            str: texte transcrit
        """
        try:
            segments, info = self.model.transcribe(
                audio_file,
                language=language or self.language,
                vad_filter=self.vad_filter,
                beam_size=5
            )
            
            text = " ".join([segment.text for segment in segments]).strip()
            
            print(f"📄 Transcription du fichier: {audio_file}")
            print(f"   Langue: {info.language} ({info.language_probability:.2f})")
            print(f"   Texte: {text}")
            
            return text
            
        except Exception as e:
            print(f"❌ Erreur lors de la transcription du fichier: {e}")
            return ""
    
    def get_model_info(self):
        """Retourne les informations sur le modèle"""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "language": self.language,
            "vad_filter": self.vad_filter
        }
