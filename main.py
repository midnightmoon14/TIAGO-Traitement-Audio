from typing import List, Dict

from tiago_assistant.ollama_client import OllamaClient
from tiago_assistant.stt_micro_only import listen_from_micro


def is_wake(text: str) -> bool:
    """
    Wake word permissif : 'tiago' suffit
    """
    t = (text or "").lower().strip()
    if not t:
        return False
    return "tiago" in t


def run():
    # ⚡ OLLAMA LOCAL — modèle texte humain
    llm = OllamaClient(
        base_url="http://127.0.0.1:11434",
        model="tiago-cesi"  # ⚠️ TON MODÈLE CUSTOM
    )

    # Vérification Ollama
    print("🔍 Vérification de la connexion Ollama...")
    try:
        import requests
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        r.raise_for_status()
        print("✅ Ollama accessible")
    except Exception as e:
        print("❌ Ollama indisponible")
        print(e)
        return

    # 🔥 Warmup (CRUCIAL)
    print("🔥 Warmup du modèle...")
    try:
        llm.chat_text(
            history=[{"role": "user", "content": "Dis simplement bonjour"}],
            temperature=0.2
        )
        print("✅ Warmup OK\n")
    except Exception as e:
        print(f"⚠️ Warmup échoué : {e}\n")

    print("=" * 60)
    print("🤖 TIAGO — Assistant vocal CESI")
    print("=" * 60)
    print("💡 Dites « Bonjour Tiago » pour commencer\n")

    while True:
        # ---- MODE VEILLE ----
        print("🎤 En attente du wake word...")
        heard = listen_from_micro(
            sample_rate=16000,
            chunk_size=4000,
            timeout_seconds=20.0,
            silence_seconds=3.0
        )

        if not heard:
            continue

        print(f"👂 Entendu : {heard}")

        if not is_wake(heard):
            continue

        print("✅ Wake word détecté")
        print("🚀 Démarrage de la conversation\n")

        history: List[Dict[str, str]] = []

        # Message d'accueil (DIRECT, HUMAIN)
        greeting = "Bonjour ! Je suis Tiago. Quel est votre projet de formation aujourd’hui ?"
        print(f"🤖 TIAGO : {greeting}\n")
        history.append({"role": "assistant", "content": greeting})

        # ---- CONVERSATION ----
        while True:
            print("🎤 À vous de parler...\n")

            user = listen_from_micro(
                sample_rate=16000,
                chunk_size=4000,
                timeout_seconds=30.0,
                silence_seconds=2.0
            )

            if not user or len(user.strip()) < 3:
                print("⚠️ Rien de clair détecté, on continue...\n")
                continue

            print(f"👤 VOUS : {user}\n")
            history.append({"role": "user", "content": user})

            try:
                response = llm.chat_text(
                    history=history,
                    temperature=0.35
                )
            except Exception as e:
                print("❌ Problème LLM :", e)
                print("🤖 TIAGO : Désolé, pouvez-vous reformuler ?\n")
                continue

            print(f"🤖 TIAGO : {response}\n")
            history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n👋 Arrêt de Tiago. À bientôt !")
