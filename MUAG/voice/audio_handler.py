"""
Audio Handler - Gestion du matériel audio (microphone/haut-parleurs)
"""
import pyaudio
import wave
import numpy as np
from collections import deque
import threading
import time
from config import (
    AUDIO_SAMPLE_RATE,
    AUDIO_CHANNELS,
    AUDIO_CHUNK_SIZE,
    AUDIO_SILENCE_THRESHOLD,
    AUDIO_SILENCE_DURATION,
    AUDIO_MIN_PHRASE_LENGTH
)


class AudioHandler:
    def __init__(self):
        self.sample_rate = AUDIO_SAMPLE_RATE
        self.channels = AUDIO_CHANNELS
        self.chunk_size = AUDIO_CHUNK_SIZE
        self.silence_threshold = AUDIO_SILENCE_THRESHOLD
        self.silence_duration = AUDIO_SILENCE_DURATION
        self.min_phrase_length = AUDIO_MIN_PHRASE_LENGTH
        
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.audio_buffer = deque(maxlen=int(self.sample_rate / self.chunk_size * 10))  # 10s buffer
        
    def list_devices(self):
        """Liste tous les périphériques audio disponibles"""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            devices.append({
                'index': i,
                'name': info['name'],
                'channels': info['maxInputChannels'],
                'sample_rate': int(info['defaultSampleRate'])
            })
        return devices
    
    def get_default_input_device(self):
        """Obtient le périphérique d'entrée par défaut"""
        try:
            return self.audio.get_default_input_device_info()
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du périphérique par défaut: {e}")
            return None
    
    def record_until_silence(self, device_index=None):
        """
        Enregistre l'audio jusqu'à ce qu'un silence soit détecté
        Returns: bytes audio data
        """
        print("🎤 Écoute en cours...")
        
        frames = []
        silent_chunks = 0
        max_silent_chunks = int(self.silence_duration * self.sample_rate / self.chunk_size)
        started_speaking = False
        
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            while True:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
                
                # Calculer le volume
                audio_data = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(audio_data).mean()
                
                if volume > self.silence_threshold:
                    started_speaking = True
                    silent_chunks = 0
                    print("🗣️ ", end="", flush=True)
                else:
                    if started_speaking:
                        silent_chunks += 1
                        print(".", end="", flush=True)
                
                # Arrêter si silence détecté après avoir parlé
                if started_speaking and silent_chunks > max_silent_chunks:
                    print("\n✅ Fin de la phrase détectée")
                    break
                
                # Timeout de sécurité (30 secondes max)
                if len(frames) > self.sample_rate / self.chunk_size * 30:
                    print("\n⏱️ Timeout atteint")
                    break
            
            stream.stop_stream()
            stream.close()
            
            # Vérifier la longueur minimale
            duration = len(frames) * self.chunk_size / self.sample_rate
            if duration < self.min_phrase_length:
                print(f"⚠️ Phrase trop courte ({duration:.1f}s)")
                return None
            
            return b''.join(frames)
            
        except Exception as e:
            print(f"❌ Erreur lors de l'enregistrement: {e}")
            return None
    
    def play_audio(self, audio_data, sample_rate=None):
        """
        Joue des données audio
        audio_data: numpy array or bytes
        """
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                output=True
            )
            
            if isinstance(audio_data, np.ndarray):
                # Convertir numpy array en bytes
                audio_data = audio_data.astype(np.int16).tobytes()
            
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"❌ Erreur lors de la lecture audio: {e}")
    
    def save_wav(self, audio_data, filename):
        """Sauvegarde l'audio en fichier WAV"""
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            print(f"💾 Audio sauvegardé: {filename}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
    
    def calibrate_silence_threshold(self, duration=3):
        """
        Calibre le seuil de silence en enregistrant l'ambiance
        duration: durée en secondes pour la calibration
        """
        print(f"🔧 Calibration du seuil de silence ({duration}s)...")
        print("   Restez silencieux...")
        
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            volumes = []
            chunks = int(duration * self.sample_rate / self.chunk_size)
            
            for _ in range(chunks):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(audio_data).mean()
                volumes.append(volume)
            
            stream.stop_stream()
            stream.close()
            
            # Calculer le seuil comme 3x la moyenne du bruit ambiant
            ambient_noise = np.mean(volumes)
            self.silence_threshold = int(ambient_noise * 3)
            
            print(f"✅ Seuil calibré: {self.silence_threshold}")
            print(f"   (Bruit ambiant: {int(ambient_noise)})")
            
            return self.silence_threshold
            
        except Exception as e:
            print(f"❌ Erreur lors de la calibration: {e}")
            return None
    
    def cleanup(self):
        """Libère les ressources audio"""
        self.audio.terminate()
