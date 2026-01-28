 # stt_micro_only_fast.py
import json
import queue
import sys
import time
import math

import pyaudio
import numpy as np
from vosk import Model, KaldiRecognizer

# CHARGEMENT DU MODÈLE UNE SEULE FOIS (au début du programme)
MODEL_PATH = "models/vosk-model-fr-0.22"  # ton nouveau modèle
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)
recognizer.SetWords(True)


def listen_from_micro(
    sample_rate: int = 16000,
    chunk_size: int = 4000,
    timeout_seconds: float = 20.0,
    silence_seconds: float = 2.0,
) -> str:
    """
    Écoute le micro (réutilise le modèle déjà chargé).
    """

    audio_interface = pyaudio.PyAudio()
    audio_queue = queue.Queue()

    def callback(in_data, frame_count, time_info, status_flags):
        audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    stream = audio_interface.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk_size,
        stream_callback=callback,
    )

    stream.start_stream()
    print("Parlez maintenant...")

    start = time.time()
    last_speech_time = None
    speech_frames = 0

    # Seuils bruit / volume
    min_rms_speech = 0.01
    target_rms = 0.05
    max_gain = 2.5

    while True:
        now = time.time()

        if now - start > timeout_seconds:
            break

        if last_speech_time is not None and (now - last_speech_time) > silence_seconds:
            break

        try:
            data = audio_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        if len(audio_np) == 0:
            continue

        rms = math.sqrt(np.mean(np.square(audio_np))) / 32768.0

        if rms < min_rms_speech:
            continue

        last_speech_time = now
        speech_frames += 1

        # Normalisation
        if rms > 0:
            gain = min(max_gain, target_rms / rms)
            audio_np *= gain
            audio_np = np.clip(audio_np, -32768, 32767)
            norm_data = audio_np.astype(np.int16).tobytes()
        else:
            norm_data = data

        if recognizer.AcceptWaveform(norm_data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "")
            if text.strip():
                print("Reconnu :", text)
                stream.stop_stream()
                stream.close()
                audio_interface.terminate()
                return text.strip()

    final = json.loads(recognizer.FinalResult())
    text = final.get("text", "")

    duration_estimee = speech_frames * chunk_size / sample_rate
    if duration_estimee < 0.5:
        text = ""

    print("Reconnu :", text if text else "(rien de clair)")

    stream.stop_stream()
    stream.close()
    audio_interface.terminate()
    return text


if __name__ == "__main__":
    print("Modèle chargé (1 seule fois). Prêt.")
    while True:
        try:
            texte = listen_from_micro()
            # Ici tu enverras 'texte' au LLM
        except KeyboardInterrupt:
            print("\nArrêt.")
            break
