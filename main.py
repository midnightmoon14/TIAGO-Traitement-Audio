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

    while True:
        # ---- WAKE MODE ----
        heard = stt.listen(seconds=3.0)
        if DEBUG:
            if heard:
                print(f"[STT-WAKE] Entendu: {heard!r}")
            else:
                print("[STT-WAKE] (silence ou trop faible)")

        if not heard or len(heard.strip()) < 2:
            continue

        # Vérifier si c'est le wake word
        if is_wake(heard):
            if DEBUG:
                print(f"[WAKE] Détection: {heard}")
            print("🔊 Wake word détecté ! Démarrage de la conversation...")
            
            # ---- Start conversation ----
            tts.say("Bonjour ! Je suis Tiago. Je peux vous aider à trouver la formation CESI la plus adaptée. Qu'est-ce que vous recherchez ?")
            time.sleep(1.0)  # évite que le micro capte la fin de la voix

            history: List[Dict[str, str]] = []

            while True:
                # Écoute pendant la conversation
                user = stt.listen(seconds=8.0)  # Augmenté pour avoir plus de temps pour parler
                if DEBUG:
                    if user:
                        print(f"[STT-USER] Entendu: {user!r}")
                    else:
                        print("[STT-USER] (silence ou trop faible)")

                if not user or len(user.strip()) < 2:
                    if DEBUG:
                        print("[STT-USER] Texte trop court ou vide, demande de répéter")
                    tts.say("Je n'ai pas bien entendu. Pouvez-vous répéter, un peu plus près du micro ?")
                    time.sleep(1.0)
                    continue

                print(f"\n[USER] {user}")
                history.append({"role": "user", "content": user})

                try:
                    obj = llm.chat_json(SYSTEM_PROMPT, history, temperature=0.2)
                    validate(obj)
                    dprint("[LLM-JSON]", obj)
                except Exception as e:
                    print("❌ erreur LLM/JSON:", e)
                    tts.say("Désolé, je n'ai pas bien compris. Pouvez-vous reformuler en précisant votre niveau et ce que vous cherchez ?")
                    time.sleep(0.8)
                    continue

                # Speak (limité 15s)
                say = limit_say(obj.get("say", ""))
                if not say:
                    # sécurité si le modèle renvoie un say vide
                    say = "D'accord. Pouvez-vous préciser votre niveau actuel et votre objectif ?"

                print(f"[TIAGO] {say}")
                tts.say(say)
                time.sleep(1.0)  # Pause après avoir parlé avant d'écouter à nouveau

                # Historique assistant (on stocke le JSON stringifié)
                history.append({"role": "assistant", "content": str(obj)})

                # Done => dataset final
                if obj.get("done") is True and obj.get("dataset") is not None:
                    print("\n=== DATASET FINAL ===")
                    print(obj["dataset"])
                    print("=====================\n")
                    tts.say("Merci ! Bonne visite au CESI Bordeaux. À bientôt !")
                    time.sleep(1.0)
                    print("\n🔄 Retour au mode veille. Dites 'Bonjour Tiago' pour recommencer.\n")
                    break  # Sort de la boucle de conversation, retour au wake mode

if __name__ == "__main__":
    run()
