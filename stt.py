# stt.py
import pyaudio
import numpy as np
from faster_whisper import WhisperModel


class STT:
    def __init__(self, model_size="small", device="cpu", compute_type="int8", samplerate=16000, input_device_index=None, volume_threshold=300):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.samplerate = samplerate
        self.input_device_index = input_device_index
        self.volume_threshold = volume_threshold  # Seuil de volume pour détecter la voix
        self.pa = pyaudio.PyAudio()

    def _get_audio_volume(self, audio_data: np.ndarray) -> float:
        """Calcule le volume RMS de l'audio"""
        return np.sqrt(np.mean(audio_data**2))

    def listen(self, seconds: float = 4.0) -> str:
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

        # Vérifier le volume avant de transcrire
        volume = np.abs(audio_i16).mean()  # Volume moyen en échelle int16
        if volume < self.volume_threshold:
            # Trop silencieux, probablement pas de voix
            return ""

        # Transcription avec VAD activé
        try:
            segments, info = self.model.transcribe(
                audio_f32,
                vad_filter=True,
                beam_size=1,  # Plus rapide, moins d'hallucinations
                condition_on_previous_text=False  # Évite les hallucinations basées sur le contexte précédent
            )

            # Récupérer les segments et filtrer
            result_texts = []
            for segment in segments:
                # Filtrer les segments avec une probabilité de "pas de voix" trop élevée
                if hasattr(segment, 'no_speech_prob') and segment.no_speech_prob > 0.5:
                    continue  # Probablement pas de voix
                text = segment.text.strip()
                # Ignorer les textes trop courts ou qui sont juste de la ponctuation
                if text and len(text) > 1 and not text.strip() in [".", ",", "!", "?", "..."]:
                    result_texts.append(text)

            result = " ".join(result_texts).strip()
            return result
        except Exception as e:
            # En cas d'erreur, retourner une chaîne vide plutôt que de planter
            return ""
