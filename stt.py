# stt.py - VERSION CORRIGÉE

import pyaudio
import numpy as np
from faster_whisper import WhisperModel
import time


class STT:
    def __init__(self, model_size="small", device="cpu", compute_type="int8", samplerate=16000, input_device_index=None):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.samplerate = samplerate
        self.input_device_index = input_device_index
        self.pa = pyaudio.PyAudio()
        
        # Seuil de volume sera calibré automatiquement
        self.volume_threshold = None
        self.noise_level = None

    def calibrate_volume(self, duration: float = 3.0) -> None:
        """
        Calibre le seuil de volume en mesurant le bruit ambiant.
        Appelez cette fonction au démarrage pendant que l'utilisateur est silencieux.
        """
        print("🔧 Calibration du micro en cours...")
        print("   ⚠️  Restez SILENCIEUX pendant 3 secondes...")
        
        chunk = 1024
        stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.samplerate,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=chunk,
        )

        volumes = []
        for _ in range(int(self.samplerate / chunk * duration)):
            data = stream.read(chunk, exception_on_overflow=False)
            audio_i16 = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_i16).mean()
            volumes.append(volume)

        stream.stop_stream()
        stream.close()

        # Niveau de bruit = moyenne + 1 écart-type
        self.noise_level = np.mean(volumes)
        # Seuil = 3x le niveau de bruit (ajustez si besoin)
        self.volume_threshold = self.noise_level * 3.0
        
        print(f"✅ Calibration terminée:")
        print(f"   📊 Bruit ambiant: {self.noise_level:.0f}")
        print(f"   🎯 Seuil de détection: {self.volume_threshold:.0f}")
        print(f"   💡 Parlez normalement, le micro est prêt !\n")

    def listen(self, seconds: float = 4.0, skip_volume_check: bool = False, show_volume: bool = False) -> str:
        """
        Écoute l'audio pendant 'seconds' secondes.
        
        Args:
            seconds: durée d'écoute
            skip_volume_check: si True, ignore le seuil de volume
            show_volume: si True, affiche le niveau audio en temps réel
        """
        chunk = 1024
        stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.samplerate,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=chunk,
        )

        frames = []
        max_volume = 0
        
        num_chunks = int(self.samplerate / chunk * seconds)
        for i in range(num_chunks):
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)
            
            # Monitoring du volume en temps réel
            if show_volume and i % 5 == 0:  # Afficher tous les 5 chunks
                audio_i16 = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(audio_i16).mean()
                max_volume = max(max_volume, volume)
                
                # Barre visuelle du volume
                bars = int(volume / 100)  # Ajustez le diviseur selon votre micro
                print(f"\r🎤 Volume: {'█' * min(bars, 40)} {volume:.0f}", end="", flush=True)

        if show_volume:
            print()  # Nouvelle ligne après la barre

        stream.stop_stream()
        stream.close()

        # Concaténer tous les frames
        audio_i16 = np.frombuffer(b"".join(frames), dtype=np.int16)
        audio_f32 = (audio_i16.astype(np.float32) / 32768.0)

        # Vérifier le volume AVANT transcription (sauf si skip)
        if not skip_volume_check:
            volume = np.abs(audio_i16).mean()
            
            if self.volume_threshold is None:
                # Pas encore calibré, utiliser un seuil par défaut bas
                threshold = 100
            else:
                threshold = self.volume_threshold
            
            if volume < threshold:
                if show_volume:
                    print(f"⚠️  Volume trop faible ({volume:.0f} < {threshold:.0f})")
                return ""

        # Transcription avec filtres agressifs
        try:
            segments, info = self.model.transcribe(
                audio_f32,
                language="fr",
                vad_filter=True,  # Très important !
                beam_size=1,
                condition_on_previous_text=False,
                initial_prompt="Bonjour Tiago, CESI, formation"
            )

            result_texts = []
            for segment in segments:
                # Filtrer les segments avec probabilité de "pas de voix" élevée
                if hasattr(segment, 'no_speech_prob') and segment.no_speech_prob > 0.4:
                    continue
                
                # Filtrer par confiance basse
                if hasattr(segment, 'avg_logprob') and segment.avg_logprob < -1.0:
                    continue
                
                text = segment.text.strip()
                
                # Filtrer texte trop court
                if len(text) < 3:
                    continue
                
                # Filtrer ponctuation seule
                if text in [".", ",", "!", "?", "...", "…"]:
                    continue
                
                # Filtrer caractères asiatiques
                if any(ord(c) > 0x3000 for c in text):
                    continue
                
                result_texts.append(text)

            result = " ".join(result_texts).strip()
            
            # Dernier filtre
            if len(result) < 2:
                return ""
            
            return result
            
        except Exception as e:
            print(f"❌ [STT-ERROR] {e}")
            return ""

    def __del__(self):
        """Ferme proprement PyAudio"""
        try:
            self.pa.terminate()
        except:
            pass