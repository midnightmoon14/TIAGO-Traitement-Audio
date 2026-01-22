# ollama_client.py

import requests
import json
import re
from typing import List, Dict, Any


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "mistral:latest"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _post_chat(self, messages: List[Dict[str, str]], temperature: float) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=180)
        r.raise_for_status()
        data = r.json()
        return data["message"]["content"]

    @staticmethod
    def _extract_json_str(text: str) -> str:
        text = text.strip()
        if text.startswith("{") and text.endswith("}"):
            return text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in model output")
        return match.group(0)

    def chat_json(
        self,
        system_prompt: str,
        history: List[Dict[str, str]],
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        messages = [{"role": "system", "content": system_prompt}] + history

        # First attempt
        content = self._post_chat(messages, temperature)
        try:
            json_str = self._extract_json_str(content)
            return json.loads(json_str)
        except Exception:
            pass

        # Repair attempt
        repair_messages = messages + [
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": (
                    "Corrige ta réponse. "
                    "Rends UNIQUEMENT un JSON valide conforme au schéma demandé, "
                    "sans aucun texte autour."
                ),
            },
        ]

        repaired = self._post_chat(repair_messages, temperature=0.0)
        json_str = self._extract_json_str(repaired)
        return json.loads(json_str)
