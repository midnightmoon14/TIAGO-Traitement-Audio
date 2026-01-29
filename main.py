from typing import List, Dict, Optional
import json

from tiago_assistant.ollama_client import OllamaClient
# from tiago_assistant.stt_micro_only import listen_from_micro
from tiago_assistant.stt import listen_from_micro
from tiago_assistant.say_audio import say_text


# Mapping des formations
FORMATIONS = {
    1: {"label": "Programme Grande Ecole", "couleur": "jaune"},
    2: {"label": "Bachelor De Specialite", "couleur": "bleu"},
    3: {"label": "Programme Executive", "couleur": "vert"},
    4: {"label": "Master Professionnel", "couleur": "rouge"}
}


def is_wake(text: str) -> bool:
    """Wake word permissif : 'tiago' suffit"""
    t = (text or "").lower().strip()
    return "tiago" in t if t else False


def build_json(say: str, done: bool = False, ask_confirmation: bool = False, 
               formation_id: Optional[int] = None, handoff: bool = False) -> Dict:
    """Construit le JSON de sortie."""
    proposed = None
    if formation_id and formation_id in FORMATIONS:
        proposed = FORMATIONS[formation_id].copy()
    
    response = {
        "say": say,
        "done": done,
        "ask_confirmation": ask_confirmation,
        "proposed": proposed,
        "int": formation_id if done else None ,  
        "handoff": handoff
    }
    
    return response


def detect_formation_from_history(history: List[Dict]) -> Optional[int]:
    """
    Analyse l'historique pour détecter quelle formation proposer.
    Retourne l'ID de la formation (1-4) ou None.
    """
    # Concaténer toute la conversation
    text = " ".join([msg["content"].lower() for msg in history])
    
    niveau = None
    objectif = None
    
    # Détecter le niveau
    if any(w in text for w in ["terminale", "lycée", "lycéen", "bac général", "sti2d"]):
        niveau = "lycee"
    elif any(w in text for w in ["bac+2", "bac+3", "prépa", "but", "bts", "licence", "bac 2", "bac 3"]):
        niveau = "bac23"
    elif any(w in text for w in ["bac+4", "master 1", "bac 4"]):
        niveau = "bac34"
    elif any(w in text for w in ["professionnel", "pro en poste", "salarié", "travaille", "emploi"]):
        niveau = "pro"
    
    # Détecter l'objectif
    if any(w in text for w in ["ingénieur", "ingénierie", "grande école", "grandes écoles"]):
        objectif = "ingenieur"
    elif any(w in text for w in ["bac+3", "bachelor", "bac 3"]):
        objectif = "bac3"
    elif any(w in text for w in ["master", "spécialisation", "bac+5", "bac+6", "bac 5", "bac 6"]):
        objectif = "master"
    elif any(w in text for w in ["formation continue", "executive"]):
        objectif = "executive"
    
    # Logique de matching
    if niveau == "lycee" and objectif == "ingenieur":
        return 1  # Programme Grande Ecole
    elif niveau == "lycee" and objectif == "bac3":
        return 2  # Bachelor De Specialite
    elif niveau in ["bac23", "bac34"] and objectif == "ingenieur":
        return 1  # Programme Grande Ecole
    elif niveau in ["bac23", "bac34"] and objectif == "master":
        return 4  # Master Professionnel
    elif niveau == "pro" or objectif == "executive":
        return 3  # Programme Executive
    
    return None


def is_confirmation(text: str) -> bool:
    """Détecte si l'utilisateur confirme."""
    text_lower = text.lower().strip()
    return any(w in text_lower for w in ["oui", "ok", "d'accord", "parfait", "allons", "vas-y", "go", "pourra"])


def needs_handoff(text: str) -> bool:
    """Détecte si la question nécessite un handoff à l'équipe."""
    text_lower = text.lower()
    keywords = ["tarif", "prix", "coût", "coute", "combien", "date", "rentrée", "inscription", "admission", "sélection"]
    return any(kw in text_lower for kw in keywords)


def run():
    llm = OllamaClient(
        base_url="http://127.0.0.1:11434",
        model="tiago-final"
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

    # Warmup
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
        formation_proposed = None
        waiting_confirmation = False

        # Message d'accueil
        greeting = "Bonjour ! Je suis Tiago. Quel est votre projet de formation aujourd'hui ?"
        greeting_json = build_json(greeting)
        say_text(greeting)
        
        print(f"📄 JSON: {json.dumps(greeting_json, ensure_ascii=False, indent=2)}")
        # print(f"🤖 TIAGO : {greeting}\n")
        history.append({"role": "assistant", "content": greeting})

        # ---- CONVERSATION ----
        turn_count = 0
        max_turns = 10
        final_formation_id = None  # ✅ AJOUT : Stocker l'ID final
        
        while turn_count < max_turns:
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
            
            # Si on attend une confirmation
            if waiting_confirmation and is_confirmation(user):
                done_msg = "Génial ! Je vous accompagne. Bonne visite !"
                done_json = build_json(
                    say=done_msg,
                    done=True,
                    formation_id=formation_proposed
                )
                say_text(done_msg)
                print(f"📄 JSON: {json.dumps(done_json, ensure_ascii=False, indent=2)}")
                # print(f"🤖 TIAGO : {done_msg}\n")
                
                final_formation_id = formation_proposed  # ✅ AJOUT : Sauvegarder l'ID
                
                print("✅ Conversation terminée, retour en veille\n")
                break
            
            history.append({"role": "user", "content": user})

            # Limiter l'historique
            if len(history) > 8:
                history = [history[0]] + history[-7:]

            # Vérifier si handoff nécessaire
            if needs_handoff(user):
                handoff_msg = "L'équipe sur place pourra vous en dire plus sur ce point !"
                handoff_json = build_json(handoff_msg, handoff=True)
                say_text(handoff_msg)
                print(f"📄 JSON: {json.dumps(handoff_json, ensure_ascii=False, indent=2)}")
                # print(f"🤖 TIAGO : {handoff_msg}\n")
                history.append({"role": "assistant", "content": handoff_msg})
                turn_count += 1
                continue

            try:
                response = llm.chat_text(
                    history=history,
                    temperature=0.35
                )
            except Exception as e:
                print("❌ Problème LLM :", e)
                error_msg = "Désolé, pouvez-vous reformuler ?"
                error_json = build_json(error_msg)
                say_text(error_msg)
                
                print(f"📄 JSON: {json.dumps(error_json, ensure_ascii=False, indent=2)}")
                # print(f"🤖 TIAGO : {error_msg}\n")
                turn_count += 1
                continue

            # Détecter si on peut proposer une formation
            formation_id = detect_formation_from_history(history + [{"role": "assistant", "content": response}])
            
            if formation_id and not waiting_confirmation:
                # On a détecté une formation, on propose
                formation = FORMATIONS[formation_id]
                propose_msg = f"Le {formation['label']} est parfait pour vous. Je vous y accompagne ?"
                
                propose_json = build_json(
                    say=propose_msg,
                    ask_confirmation=True,
                    formation_id=formation_id
                )
                say_text(propose_msg)
                
                print(f"📄 JSON: {json.dumps(propose_json, ensure_ascii=False, indent=2)}")
                # print(f"🤖 TIAGO : {propose_msg}\n")
                history.append({"role": "assistant", "content": propose_msg})
                
                formation_proposed = formation_id
                waiting_confirmation = True
                turn_count += 1
                continue
            
            # Réponse normale
            response_json = build_json(say=response)
            say_text(response)
            
            print(f"📄 JSON: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
            # print(f"🤖 TIAGO : {response}\n")
            history.append({"role": "assistant", "content": response})
            turn_count += 1

        if turn_count >= max_turns:
            print("⏰ Conversation trop longue, retour en veille\n")
        
        # ✅ AJOUT : Retourner l'ID final
        if final_formation_id:
            print(f"🎯 FORMATION FINALE : {final_formation_id} - {FORMATIONS[final_formation_id]['label']}\n")
            return final_formation_id  # Retourne l'ID à la fin de la conversation


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n👋 Arrêt de Tiago. À bientôt !")


