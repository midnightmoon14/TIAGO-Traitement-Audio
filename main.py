import time
from typing import List, Dict

from prompts import SYSTEM_PROMPT
from ollama_client import OllamaClient
from stt import STT
from tts import TTS
from validator import validate

DEBUG = True
MAX_CHARS = 220

def dprint(*args):
    if DEBUG:
        print(*args)

def limit_say(text: str) -> str:
    text = (text or "").strip()
    if len(text) <= MAX_CHARS:
        return text
    cut = text[:MAX_CHARS]
    if "." in cut:
        cut = cut.rsplit(".", 1)[0] + "."
    return cut + " …"

def is_wake(text: str) -> bool:
    t = (text or "").lower()
    return ("tiago" in t) and (("bonjour" in t) or ("salut" in t) or ("hey" in t))

def run():
    llm = OllamaClient(base_url="http://127.0.0.1:11434", model="mistral:latest")
    stt = STT(model_size="small", device="cpu", compute_type="int8")
    tts = TTS(rate=175)

    print("✅ TIAGO prêt. Dis: 'Bonjour Tiago' pour commencer.")

    wake_hits = 0  # pour réduire les faux déclenchements

    while True:
        # ---- WAKE MODE ----
        heard = stt.listen(seconds=2.8)
        dprint(f"[STT-WAKE] {heard!r}")

        if not heard or len(heard.strip()) < 2:
            wake_hits = 0
            continue

        # Affiche seulement si tiago est entendu
        if "tiago" in heard.lower():
            dprint("[wake-heard]", heard)

        if is_wake(heard):
            wake_hits += 1
        else:
            wake_hits = 0
            continue

        # Exige 2 hits consécutifs pour éviter le bruit
        if wake_hits < 2:
            continue
        wake_hits = 0

        # ---- Start conversation ----
        tts.say("Bonjour ! Je suis Tiago. Je peux vous aider à trouver la formation CESI la plus adaptée. Qu’est-ce que vous recherchez ?")
        time.sleep(0.8)  # évite que le micro capte la fin de la voix

        history: List[Dict[str, str]] = []

        while True:
            user = stt.listen(seconds=6.0)
            dprint(f"[STT-USER] {user!r}")

            if not user or len(user.strip()) < 2:
                tts.say("Je n'ai pas bien entendu. Pouvez-vous répéter, un peu plus près du micro ?")
                time.sleep(0.8)
                continue

            print("[user]", user)
            history.append({"role": "user", "content": user})

            try:
                obj = llm.chat_json(SYSTEM_PROMPT, history, temperature=0.2)
                validate(obj)
                dprint("[LLM-JSON]", obj)
            except Exception as e:
                print("❌ erreur LLM/JSON:", e)
                tts.say("Désolé, je n’ai pas bien compris. Pouvez-vous reformuler en précisant votre niveau et ce que vous cherchez ?")
                time.sleep(0.8)
                continue

            # Speak (limité 15s)
            say = limit_say(obj.get("say", ""))
            if not say:
                # sécurité si le modèle renvoie un say vide
                say = "D'accord. Pouvez-vous préciser votre niveau actuel et votre objectif ?"

            tts.say(say)
            time.sleep(0.8)

            # Historique assistant (on stocke le JSON stringifié)
            history.append({"role": "assistant", "content": str(obj)})

            # Done => dataset final
            if obj.get("done") is True and obj.get("dataset") is not None:
                print("\n=== DATASET FINAL ===")
                print(obj["dataset"])
                print("=====================\n")
                tts.say("Merci ! Bonne visite au CESI Bordeaux. À bientôt !")
                time.sleep(0.8)
                break

            time.sleep(0.15)

if __name__ == "__main__":
    run()
