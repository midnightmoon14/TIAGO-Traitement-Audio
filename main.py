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
    """
    Wake word plus permissif: juste "tiago" suffit maintenant
    (ou "tiago" + mot de salutation)
    """
    t = (text or "").lower().strip()
    if not t:
        return False
    
    # Accepter juste "tiago" ou "tiago" avec salutation
    if "tiago" in t:
        return True
    
    # Variantes courantes
    wake_words = ["bonjour tiago", "salut tiago", "hey tiago", "coucou tiago", 
                  "bonsoir tiago", "allo tiago", "ok tiago"]
    return any(w in t for w in wake_words)

def run():
    # OPTION 1: Mistral 7B (plus rapide, toujours bon en français)
    llm = OllamaClient(base_url="http://127.0.0.1:11434", model="mistral:7b")
    
    # OPTION 2: Si vous voulez encore plus rapide, essayez Phi-3 mini
    # llm = OllamaClient(base_url="http://127.0.0.1:11434", model="phi3:mini")
    
    # OPTION 3: Pour garder mistral:latest (mais plus lent)
    # llm = OllamaClient(base_url="http://127.0.0.1:11434", model="mistral:latest")
    
    stt = STT(model_size="small", device="cpu", compute_type="int8")
    tts = TTS(rate=175)

    print("=" * 60)
    print("🤖 TIAGO - Assistant vocal CESI")
    print("=" * 60)
    
    # CALIBRATION AUTOMATIQUE AU DÉMARRAGE
    stt.calibrate_volume(duration=3.0)
    
    print("✅ TIAGO est prêt !")
    print("💡 Dites 'Bonjour Tiago' ou 'Hey Tiago' pour commencer.\n")

    while True:
        # ---- WAKE MODE ----
        print("🎤 En attente du wake word...")
        heard = stt.listen(seconds=3.0, skip_volume_check=False, show_volume=DEBUG)
        
        if heard:
            print(f"👂 Détecté: '{heard}'")
        
        if not heard or len(heard.strip()) < 2:
            continue

        # Vérifier si c'est le wake word
        if is_wake(heard):
            print(f"✅ Wake word détecté: '{heard}'")
            print("🚀 Démarrage de la conversation...\n")
            
            # IMPORTANT: petite pause avant que Tiago parle
            time.sleep(0.5)
            
            tts.say("Bonjour ! Je suis Tiago. Je peux vous aider à trouver la formation CESI la plus adaptée. Qu'est-ce que vous recherchez ?")
            
            # CRUCIAL: attendre que le TTS finisse + 2 secondes de pause
            # pour éviter que le micro capte la fin de la voix de Tiago
            time.sleep(2.0)

            history: List[Dict[str, str]] = []
            conversation_active = True

            while conversation_active:
                print("\n🎤 À vous de parler (vous avez 8 secondes)...")
                
                # Écoute avec feedback visuel
                user = stt.listen(seconds=8.0, show_volume=DEBUG)
                
                if user:
                    print(f"✅ Vous avez dit: '{user}'\n")
                else:
                    print("⚠️  Rien détecté ou volume trop faible")

                # Si silence ou texte trop court
                if not user or len(user.strip()) < 3:
                    print("⚠️  Texte trop court, je demande de répéter...\n")
                    tts.say("Je n'ai pas bien entendu. Pouvez-vous répéter un peu plus fort ?")
                    time.sleep(2.0)  # Pause après TTS
                    continue

                print(f"[USER] {user}")
                history.append({"role": "user", "content": user})

                # Appel au LLM avec DEBUG DÉTAILLÉ
                try:
                    print("🔄 Envoi au LLM Mistral...")
                    print(f"   📝 Historique: {len(history)} messages")
                    
                    obj = llm.chat_json(SYSTEM_PROMPT, history, temperature=0.2)
                    
                    print(f"✅ Réponse LLM reçue: {obj}")
                    print("🔍 Validation en cours...")
                    
                    validate(obj)
                    
                    print("✅ Validation OK")
                    dprint("[LLM-JSON]", obj)
                    
                except Exception as e:
                    print(f"❌ ERREUR DÉTAILLÉE:")
                    print(f"   Type: {type(e).__name__}")
                    print(f"   Message: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    tts.say("Désolé, j'ai eu un problème technique. Pouvez-vous reformuler ?")
                    time.sleep(2.0)
                    continue

                # Préparer la réponse
                say = limit_say(obj.get("say", ""))
                if not say:
                    say = "D'accord. Pouvez-vous préciser votre niveau actuel et votre objectif ?"

                print(f"[TIAGO] {say}\n")
                tts.say(say)
                
                # CRUCIAL: pause après chaque réponse de Tiago
                time.sleep(2.0)

                # Historique assistant
                history.append({"role": "assistant", "content": str(obj)})

                # Vérifier si terminé
                if obj.get("done") is True and obj.get("dataset") is not None:
                    print("\n" + "=" * 60)
                    print("📊 DATASET FINAL")
                    print("=" * 60)
                    print(obj["dataset"])
                    print("=" * 60 + "\n")
                    
                    tts.say("Merci ! Bonne visite au CESI Bordeaux. À bientôt !")
                    time.sleep(2.0)
                    
                    print("🔄 Retour au mode veille.")
                    print("💡 Dites 'Bonjour Tiago' pour recommencer.\n")
                    conversation_active = False
                    break

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt de Tiago. À bientôt !")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        raise