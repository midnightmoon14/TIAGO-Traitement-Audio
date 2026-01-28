# stt.py - VERSION OPTIMISÉE (inspirée de Vosk)

import pyaudio
import numpy as np
from faster_whisper import WhisperModel
import time
import math


class STT:
    def __init__(self, model_size="small", device="cpu", compute_type="int8", samplerate=16000, input_device_index=None):
        # Modèle Whisper chargé UNE SEULE FOIS (comme Vosk)
        print("🔧 Chargement du modèle Whisper...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.samplerate = samplerate
        self.input_device_index = input_device_index
        self.pa = pyaudio.PyAudio()
        
        # Seuils de volume calibrés automatiquement
        self.volume_threshold = None
        self.noise_level = None
        
        # Paramètres de normalisation audio (inspirés de Vosk)
        self.min_rms_speech = 0.01  # Seuil minimum RMS pour considérer comme parole
        self.target_rms = 0.05      # RMS cible pour normalisation
        self.max_gain = 2.5         # Gain maximum pour éviter la distorsion

    def calibrate_volume(self, duration: float = 2.0) -> None:
        """
        Calibre le seuil de volume en mesurant le bruit ambiant (RMS au lieu de moyenne absolue).
        """
        print("🔧 Calibration micro (2 secondes)...")
        print("   ⚠️  Restez SILENCIEUX...")
        
        chunk = 1024
        stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.samplerate,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=chunk,
        )

        rms_values = []
        for i in range(int(self.samplerate / chunk * duration)):
            try:
                data = stream.read(chunk, exception_on_overflow=False)
                audio_i16 = np.frombuffer(data, dtype=np.int16)
                audio_f32 = audio_i16.astype(np.float32) / 32768.0
                # Utiliser RMS (Root Mean Square) comme Vosk pour meilleure détection
                rms = math.sqrt(np.mean(np.square(audio_f32)))
                rms_values.append(rms)
                
                # Afficher feedback en temps réel
                if i % 3 == 0:
                    print(f"\r   📊 Mesure RMS: {rms:.4f}", end="", flush=True)
            except:
                pass

        print()  # Nouvelle ligne
        stream.stop_stream()
        stream.close()

        # Calcul seuil basé sur RMS
        if len(rms_values) == 0 or max(rms_values) < 0.001:
            print("⚠️  MICRO SILENCIEUX ! Vérifiez vos paramètres Windows.")
            print("   Paramètres → Son → Entrée → Testez votre micro")
            self.noise_level = 0.01
            self.volume_threshold = 0.03
        else:
            self.noise_level = np.mean(rms_values)
            # Seuil = 3x le bruit RMS (plus précis que moyenne absolue)
            self.volume_threshold = max(self.noise_level * 3.0, self.min_rms_speech)
        
        print(f"✅ Calibration OK:")
        print(f"   📊 Bruit RMS: {self.noise_level:.4f}")
        print(f"   🎯 Seuil RMS: {self.volume_threshold:.4f}\n")

    def _normalize_audio(self, audio_i16: np.ndarray) -> np.ndarray:
        """
        Normalise l'audio pour améliorer la reconnaissance (inspiré de Vosk).
        """
        audio_f32 = audio_i16.astype(np.float32) / 32768.0
        rms = math.sqrt(np.mean(np.square(audio_f32)))
        
        if rms < self.min_rms_speech:
            return audio_f32
        
        # Normalisation avec gain adaptatif
        if rms > 0:
            gain = min(self.max_gain, self.target_rms / rms)
            audio_f32 *= gain
            audio_f32 = np.clip(audio_f32, -1.0, 1.0)
        
        return audio_f32

    def listen(
        self, 
        silence_duration: float = 5.0, 
        timeout_seconds: float = 30.0,
        skip_volume_check: bool = False, 
        show_volume: bool = False
    ) -> str:
        """
        Écoute l'audio jusqu'à détecter un silence de 'silence_duration' secondes.
        Optimisé avec timeout et normalisation audio.
        
        Args:
            silence_duration: durée de silence (en secondes) avant d'arrêter l'écoute
            timeout_seconds: timeout maximum pour éviter les boucles infinies
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
        start_time = time.time()
        last_speech_time = None
        chunks_per_second = int(self.samplerate / chunk)
        silence_chunks_threshold = int(chunks_per_second * silence_duration)
        silence_chunks_count = 0
        
        # Déterminer le seuil RMS
        if self.volume_threshold is None:
            threshold_rms = self.min_rms_speech
        else:
            threshold_rms = self.volume_threshold
        
        print(f"🎤 Écoute en cours... (parlez, silence de {silence_duration}s pour terminer, max {timeout_seconds}s)")
        
        while True:
            now = time.time()
            
            # Timeout global pour éviter les boucles infinies
            if now - start_time > timeout_seconds:
                if show_volume:
                    print()
                print(f"⏱️  Timeout atteint ({timeout_seconds}s)")
                break
            
            # Timeout de silence (comme Vosk)
            if last_speech_time is not None and (now - last_speech_time) > silence_duration:
                if show_volume:
                    print()
                print(f"✅ Silence de {silence_duration} secondes détecté, arrêt de l'écoute.")
                break
            
            try:
                data = stream.read(chunk, exception_on_overflow=False)
            except:
                break
            
            if len(data) == 0:
                continue
            
            frames.append(data)
            
            # Convertir en numpy et calculer RMS (comme Vosk)
            audio_i16 = np.frombuffer(data, dtype=np.int16)
            audio_f32 = audio_i16.astype(np.float32) / 32768.0
            rms = math.sqrt(np.mean(np.square(audio_f32)))
            
            # Monitoring du volume en temps réel (afficher moins souvent)
            if show_volume and len(frames) % 10 == 0:
                bars = int(rms * 1000)  # Ajuster pour RMS
                status = "🔊" if rms >= threshold_rms else "🔇"
                elapsed = int(now - start_time)
                print(f"\r{status} RMS: {rms:.4f} | Silence: {silence_chunks_count}/{silence_chunks_threshold} | Temps: {elapsed}s   ", end="", flush=True)
            
            # Détecter si on est en silence ou en parole (basé sur RMS)
            if rms >= threshold_rms:
                # Parole détectée, réinitialiser le compteur de silence
                silence_chunks_count = 0
                last_speech_time = now
            else:
                # Silence détecté, incrémenter le compteur
                silence_chunks_count += 1

        if show_volume:
            print()  # Nouvelle ligne après la barre

        stream.stop_stream()
        stream.close()

        # Vérifier qu'on a capturé quelque chose
        if len(frames) == 0:
            return ""

        # Concaténer tous les frames et normaliser
        audio_i16 = np.frombuffer(b"".join(frames), dtype=np.int16)
        
        # Vérifier le volume AVANT transcription (sauf si skip)
        if not skip_volume_check:
            audio_f32_test = audio_i16.astype(np.float32) / 32768.0
            rms_test = math.sqrt(np.mean(np.square(audio_f32_test)))
            
            if rms_test < threshold_rms:
                if show_volume:
                    print(f"⚠️  Volume trop faible (RMS: {rms_test:.4f} < {threshold_rms:.4f})")
                return ""
        
        # Normaliser l'audio pour améliorer la reconnaissance
        audio_f32 = self._normalize_audio(audio_i16)

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
