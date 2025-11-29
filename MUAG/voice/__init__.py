"""
Voice Package - Interface vocale complète (STT/TTS)
"""
from .voice_manager import VoiceManager
from .stt_engine import STTEngine
from .tts_engine import TTSEngine
from .audio_handler import AudioHandler

__all__ = [
    'VoiceManager',
    'STTEngine',
    'TTSEngine',
    'AudioHandler'
]
