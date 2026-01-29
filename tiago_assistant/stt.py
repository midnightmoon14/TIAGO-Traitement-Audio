# tiago_assistant/stt.py  (Option A: arecord hw:2,0)

import json
import queue
import time
import math
import subprocess
from typing import Optional

import numpy as np
from vosk import Model, KaldiRecognizer

MODEL_PATH = "models/vosk-model-fr-0.22"

_model = None
_recognizer = None

def _get_recognizer():
    global _model, _recognizer
    if _recognizer is None:
        _model = Model(MODEL_PATH)
        _recognizer = KaldiRecognizer(_model, 16000)
        _recognizer.SetWords(True)
    return _recognizer


def listen_from_micro(
    sample_rate: int = 16000,
    chunk_size: int = 4000,
    timeout_seconds: float = 20.0,
    silence_seconds: float = 2.0,
    device_alsa: str = "hw:2,0",   # ✅ ton device Linux
) -> str:
    """
    Capture micro via arecord (ALSA), pas de PyAudio.
    Retourne le texte reconnu.
    """
    recognizer = _get_recognizer()

    cmd = [
        "arecord",
        "-D", device_alsa,
        "-f", "S16_LE",
        "-c", "1",
        "-r", str(sample_rate),
        "-t", "raw",
        "-q",  # quiet
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        raise RuntimeError("arecord introuvable. Installe alsa-utils: sudo apt install alsa-utils")

    start = time.time()
    last_speech_time: Optional[float] = None
    speech_frames = 0

    min_rms_speech = 0.01
    target_rms = 0.05
    max_gain = 2.5

    print("Parlez maintenant...")

    try:
        while True:
            now = time.time()

            if now - start > timeout_seconds:
                break

            if last_speech_time is not None and (now - last_speech_time) > silence_seconds:
                break

            data = proc.stdout.read(chunk_size * 2)  # int16 -> 2 bytes
            if not data:
                continue

            audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            if len(audio_np) == 0:
                continue

            rms = math.sqrt(np.mean(np.square(audio_np))) / 32768.0
            if rms < min_rms_speech:
                continue

            last_speech_time = now
            speech_frames += 1

            # Normalisation légère
            gain = min(max_gain, target_rms / rms) if rms > 0 else 1.0
            audio_np *= gain
            audio_np = np.clip(audio_np, -32768, 32767)
            norm_data = audio_np.astype(np.int16).tobytes()

            if recognizer.AcceptWaveform(norm_data):
                result = json.loads(recognizer.Result())
                text = (result.get("text") or "").strip()
                if text:
                    print("Reconnu :", text)
                    return text

        final = json.loads(recognizer.FinalResult())
        text = (final.get("text") or "").strip()

        duration_estimee = speech_frames * chunk_size / sample_rate
        if duration_estimee < 0.5:
            text = ""

        print("Reconnu :", text if text else "(rien de clair)")
        return text

    finally:
        try:
            proc.terminate()
        except Exception:
            pass
