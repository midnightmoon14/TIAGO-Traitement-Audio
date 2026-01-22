# stt.py
import pyaudio
import numpy as np
from faster_whisper import WhisperModel


class STT:
    def __init__(self, model_size="small", device="cpu", compute_type="int8", samplerate=16000, input_device_index=None):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.samplerate = samplerate
        self.input_device_index = input_device_index
        self.pa = pyaudio.PyAudio()

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

        segments, _ = self.model.transcribe(audio_f32, vad_filter=True)
        return " ".join(seg.text.strip() for seg in segments).strip()
