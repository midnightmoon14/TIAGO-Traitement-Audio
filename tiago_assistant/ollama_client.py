# ollama_client.py

import requests
from typing import List, Dict, Any


class OllamaClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "tiago-cesi"
    ):
        """
        Client Ollama pour LLM local.

        Le modèle retourne UNIQUEMENT du texte.
        Le JSON est construit côté main.py.
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.debug = True
        self._warmed = False

    # ------------------------------------------------------------------
    # MODE TEXTE (UTILISÉ PAR LE PROJET)
    # ------------------------------------------------------------------
    def chat_text(
        self,
        history: List[Dict[str, str]],
        temperature: float = 0.35
    ) -> str:
        """
        Envoie l'historique au modèle et retourne UNE réponse texte courte.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": history,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "temperature": temperature,
                "num_predict": 80,        # réponses courtes
                "top_p": 0.9,
                "repeat_penalty": 1.25,
                "num_ctx": 1024
            }
        }

        if self.debug:
            print("📤 Envoi TEXTE à Ollama")
            print(f"   Model: {self.model}")
            print(f"   Messages: {len(history)}")
            print(f"   Dernier message: {history[-1]['content']}")

        timeout = 180 if not self._warmed else 60

        r = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=timeout
        )
        r.raise_for_status()

        content = r.json()["message"]["content"].strip()

        if self.debug:
            print(f"📥 Réponse reçue: {content}")

        self._warmed = True
        return content

    # ------------------------------------------------------------------
    # MODE JSON (NON UTILISÉ ACTUELLEMENT – CONSERVÉ SI BESOIN)
    # ------------------------------------------------------------------
    def chat_json(
        self,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None,
        temperature: float = 0.2
    ):
        """
        Ancien mode JSON.
        ⚠️ Non utilisé dans la version actuelle du projet.
        """
        raise RuntimeError(
            "chat_json() n'est plus utilisé. "
            "Le modèle retourne du texte, le JSON est construit dans main.py."
        )
