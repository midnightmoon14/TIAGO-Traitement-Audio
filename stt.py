# stt.py
import pyaudio
import numpy as np
from faster_whisper import WhisperModel


class STT:
    def __init__(self, model_size="small", device="cpu", compute_type="int8", samplerate=16000, input_device_index=None, volume_threshold=400):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.samplerate = samplerate
        self.input_device_index = input_device_index
        self.volume_threshold = volume_threshold  # Seuil de volume augmenté pour éviter les faux positifs
        self.pa = pyaudio.PyAudio()

    def _get_audio_volume(self, audio_data: np.ndarray) -> float:
        """Calcule le volume RMS de l'audio"""
        return np.sqrt(np.mean(audio_data**2))

    def listen(self, seconds: float = 4.0, skip_volume_check: bool = False) -> str:
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
        for _ in range(int(self.samplerate / chunk * seconds)):
            frames.append(stream.read(chunk, exception_on_overflow=False))

        stream.stop_stream()
        stream.close()

        audio_i16 = np.frombuffer(b"".join(frames), dtype=np.int16)
        audio_f32 = (audio_i16.astype(np.float32) / 32768.0)

        # Vérifier le volume avant de transcrire (sauf si skip_volume_check=True)
        if not skip_volume_check:
            volume = np.abs(audio_i16).mean()  # Volume moyen en échelle int16
            if volume < self.volume_threshold:
                # Trop silencieux, probablement pas de voix
                return ""

        # Transcription avec VAD activé et langue française forcée
        try:
            segments, info = self.model.transcribe(
                audio_f32,
                language="fr",  # FORCER le français pour éviter les hallucinations multilingues
                vad_filter=True,
                beam_size=1,
                condition_on_previous_text=False,
                initial_prompt="Bonjour Tiago"  # Aide le modèle à mieux comprendre le contexte
            )

            # Récupérer les segments et filtrer AGGRESSIVEMENT
            result_texts = []
            for segment in segments:
                # Filtrer très strictement : probabilité de "pas de voix" doit être très faible
                if hasattr(segment, 'no_speech_prob') and segment.no_speech_prob > 0.3:
                    continue  # Trop de probabilité que ce ne soit pas de la voix
                
                # Filtrer par probabilité de confiance (si disponible)
                if hasattr(segment, 'probability') and segment.probability < 0.5:
                    continue  # Probabilité trop faible
                
                text = segment.text.strip()
                
                # Filtrer les textes trop courts (minimum 3 caractères)
                if not text or len(text) < 3:
                    continue
                
                # Filtrer la ponctuation seule
                if text.strip() in [".", ",", "!", "?", "...", "。", "，", "！", "？"]:
                    continue
                
                # Filtrer les caractères non-français suspects (chinois, japonais, etc.)
                # Vérifier s'il y a des caractères asiatiques (chinois, japonais, coréen)
                suspicious_ranges = [
                    range(0x4E00, 0x9FFF),  # Chinois
                    range(0x3040, 0x309F),  # Hiragana
                    range(0x30A0, 0x30FF),  # Katakana
                    range(0xAC00, 0xD7AF),  # Coréen
                ]
                has_asian_chars = any(ord(c) in r for c in text for r in suspicious_ranges)
                if has_asian_chars:
                    continue  # Ignorer les textes avec caractères asiatiques
                
                result_texts.append(text)

            result = " ".join(result_texts).strip()
            
            # Dernier filtre : si le résultat est trop court ou suspect, retourner vide
            if len(result) < 2:
                return ""
            
            return result
        except Exception as e:
            # En cas d'erreur, retourner une chaîne vide plutôt que de planter
            print(f"[STT-ERROR] {e}")
            return ""
