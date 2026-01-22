# tts.py

import pyttsx3


class TTS:
    def __init__(self, rate: int = 175):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)

    def say(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()
