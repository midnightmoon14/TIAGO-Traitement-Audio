# tiago_assistant.py - Classe principale pour l'assistant vocal TIAGO

from typing import Dict, List, Any
import numpy as np
from stt import STT
from prompts import SYSTEM_PROMPT
from validator import validate


class TiagoAssistant:
    """
    Assistant vocal TIAGO pour la JPO du CESI Bordeaux.
    
    Cette classe gère le pipeline complet :
    1. STT (Speech-to-Text) : audio → texte
    2. LLM (Language Model) : texte → réponse intelligente
    3. Validation : vérification du JSON de sortie
    
    Usage:
        # Initialisation
        from ollama_client import OllamaClient
        llm = OllamaClient(base_url="http://127.0.0.1:11434", model="mistral:7b")
        tiago = TiagoAssistant(llm_client=llm)
        
        # Démarrer conversation
        greeting = tiago.start_conversation()
        robot.speak(greeting['say'])
        
        # Boucle conversation
        while True:
            audio_bytes = robot.record_audio(seconds=5)
            response = tiago.process_audio(audio_bytes)
            
            robot.speak(response['say'])
            
            if response['done']:
                robot.take_brochure(response['dataset']['couleur'])
                break
    """
    
    def __init__(
        self,
        llm_client,
        stt_model_size: str = "small",
        stt_device: str = "cpu",
        stt_compute_type: str = "int8",
        input_device_index: int = None,
        debug: bool = True
    ):
        """
        Initialise l'assistant TIAGO.
        
        Args:
            llm_client: Client LLM (OllamaClient - local uniquement)
            stt_model_size: Taille du modèle Whisper ("tiny", "small", "medium")
            stt_device: Device pour Whisper ("cpu" ou "cuda")
            stt_compute_type: Type de compute ("int8", "float16", "float32")
            input_device_index: Index du micro (None = micro par défaut)
            debug: Active les logs détaillés
        """
        self.llm = llm_client
        self.debug = debug
        
        # Initialisation STT (Speech-to-Text)
        if self.debug:
            print("🔧 Initialisation STT (Whisper)...")
        
        self.stt = STT(
            model_size=stt_model_size,
            device=stt_device,
            compute_type=stt_compute_type,
            input_device_index=input_device_index
        )
        
        # Historique de conversation (vide au départ)
        self.conversation_history: List[Dict[str, str]] = []
        
        if self.debug:
            print("✅ TIAGO initialisé avec succès\n")
    
    def start_conversation(self) -> Dict[str, Any]:
        """
        Démarre une nouvelle conversation.
        Reset l'historique et renvoie le message d'accueil.
        
        Returns:
            dict: {
                "say": "Bonjour ! Comment je peux vous aider ?",
                "done": False,
                "ask_confirmation": False,
                "proposed": None,
                "dataset": None,
                "handoff": False
            }
        """
        # Reset historique
        self.conversation_history = []
        
        if self.debug:
            print("🚀 Nouvelle conversation démarrée")
        
        # Message d'accueil
        greeting = {
            "say": "Bonjour ! Comment je peux vous aider pour votre projet d'études ?",
            "done": False,
            "ask_confirmation": False,
            "proposed": None,
            "dataset": None,
            "handoff": False
        }
        
        return greeting
    
    def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Traite un tour de conversation complet.
        
        Pipeline :
        1. STT : convertit l'audio en texte
        2. LLM : génère une réponse intelligente en JSON
        3. Validation : vérifie que le JSON est correct
        4. Historique : sauvegarde l'échange
        
        Args:
            audio_data: Audio brut en bytes (format WAV attendu)
        
        Returns:
            dict: {
                "say": "Texte à faire dire au robot",
                "done": bool,  # True si conversation terminée
                "ask_confirmation": bool,
                "proposed": {"label": "...", "couleur": "..."} ou None,
                "dataset": {"couleur": "...", "quantite": 1} ou None,  # Si done=True
                "handoff": bool  # True si question hors sujet
            }
        
        Raises:
            Exception: Si le STT échoue, le LLM plante, ou la validation rate
        """
        # ──────────────────────────────────────────────────────
        # ÉTAPE 1 : STT (Audio → Texte)
        # ──────────────────────────────────────────────────────
        if self.debug:
            print("\n🎤 Transcription audio...")
        
        try:
            # Convertir bytes en numpy array pour Whisper
            # Supposons que audio_data est déjà au bon format (16kHz, mono, int16)
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcription avec filtres
            user_text = self._transcribe_with_stt(audio_array)
            
            if not user_text or len(user_text.strip()) < 2:
                if self.debug:
                    print("⚠️  Transcription vide ou trop courte")
                
                # Retourner une réponse par défaut
                return {
                    "say": "Je n'ai pas bien entendu. Pouvez-vous répéter ?",
                    "done": False,
                    "ask_confirmation": False,
                    "proposed": None,
                    "dataset": None,
                    "handoff": False
                }
            
            if self.debug:
                print(f"✅ Transcription : '{user_text}'")
        
        except Exception as e:
            if self.debug:
                print(f"❌ Erreur STT : {e}")
            raise Exception(f"STT failed: {e}")
        
        # ──────────────────────────────────────────────────────
        # ÉTAPE 2 : LLM (Texte → JSON)
        # ──────────────────────────────────────────────────────
        if self.debug:
            print(f"🤖 Envoi au LLM...")
        
        try:
            # Ajouter le message utilisateur à l'historique AVANT l'appel LLM
            self.conversation_history.append({
                "role": "user",
                "content": user_text
            })
            
            # Appel LLM
            response = self.llm.chat_json(
                system_prompt=SYSTEM_PROMPT,
                history=self.conversation_history,
                temperature=0.2
            )
            
            if self.debug:
                print(f"✅ Réponse LLM reçue")
        
        except Exception as e:
            if self.debug:
                print(f"❌ Erreur LLM : {e}")
            raise Exception(f"LLM failed: {e}")
        
        # ──────────────────────────────────────────────────────
        # ÉTAPE 3 : VALIDATION
        # ──────────────────────────────────────────────────────
        if self.debug:
            print("🔍 Validation JSON...")
        
        try:
            validate(response)
            
            if self.debug:
                print("✅ Validation OK")
        
        except Exception as e:
            if self.debug:
                print(f"❌ Validation échouée : {e}")
            raise Exception(f"Validation failed: {e}")
        
        # ──────────────────────────────────────────────────────
        # ÉTAPE 4 : HISTORIQUE
        # ──────────────────────────────────────────────────────
        # Ajouter la réponse assistant à l'historique
        self.conversation_history.append({
            "role": "assistant",
            "content": str(response)
        })
        
        if self.debug:
            print(f"\n[TIAGO] {response['say']}")
            if response['done']:
                print(f"✅ Conversation terminée : {response['dataset']}")
        
        return response
    
    def _transcribe_with_stt(self, audio_array: np.ndarray) -> str:
        """
        Transcrit l'audio avec le STT (méthode interne).
        
        Args:
            audio_array: Audio en numpy array (float32, normalisé)
        
        Returns:
            str: Texte transcrit (ou "" si vide)
        """
        try:
            segments, info = self.stt.model.transcribe(
                audio_array,
                language="fr",
                vad_filter=True,
                beam_size=1,
                condition_on_previous_text=False,
                initial_prompt="Bonjour Tiago, CESI, formation"
            )
            
            # Récupérer et filtrer les segments
            result_texts = []
            for segment in segments:
                # Filtrer les segments avec probabilité de "pas de voix" élevée
                if hasattr(segment, 'no_speech_prob') and segment.no_speech_prob > 0.4:
                    continue
                
                text = segment.text.strip()
                
                # Filtrer texte trop court ou ponctuation seule
                if len(text) < 3 or text in [".", ",", "!", "?", "..."]:
                    continue
                
                # Filtrer caractères asiatiques
                if any(ord(c) > 0x3000 for c in text):
                    continue
                
                result_texts.append(text)
            
            return " ".join(result_texts).strip()
        
        except Exception as e:
            if self.debug:
                print(f"⚠️  Erreur transcription : {e}")
            return ""
    
    def get_conversation_length(self) -> int:
        """
        Retourne le nombre de tours de conversation.
        
        Returns:
            int: Nombre de messages (user + assistant)
        """
        return len(self.conversation_history)
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Retourne l'historique complet de la conversation.
        
        Returns:
            list: Historique [{"role": "user", "content": "..."}, ...]
        """
        return self.conversation_history.copy()
    
    def reset(self):
        """Reset complet de l'assistant (historique + état)."""
        self.conversation_history = []
        if self.debug:
            print("🔄 Assistant reset")


