# ollama_client.py - VERSION DEBUG

import requests
import json
import re
from typing import List, Dict, Any


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "mistral:latest"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.debug = True  # Activer le debug

    def _post_chat(self, messages: List[Dict[str, str]], temperature: float) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        
        if self.debug:
            print(f"📤 Envoi à Ollama:")
            print(f"   Model: {self.model}")
            print(f"   Messages: {len(messages)}")
            print(f"   Dernier message: {messages[-1]['content'][:100]}...")
        
        try:
            r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=180)
            r.raise_for_status()
            data = r.json()
            content = data["message"]["content"]
            
            if self.debug:
                print(f"📥 Réponse Ollama reçue ({len(content)} chars)")
                print(f"   Aperçu: {content[:200]}...")
            
            return content
            
        except requests.exceptions.Timeout:
            print("❌ TIMEOUT: Ollama met trop de temps à répondre (>180s)")
            raise
        except requests.exceptions.ConnectionError:
            print("❌ ERREUR CONNEXION: Ollama n'est pas accessible")
            print(f"   Vérifiez que Ollama tourne sur {self.base_url}")
            raise
        except Exception as e:
            print(f"❌ ERREUR POST: {e}")
            raise

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
        print("🤖 Tentative 1/2: génération JSON...")
        content = self._post_chat(messages, temperature)
        
        try:
            if self.debug:
                print("🔍 Extraction JSON...")
                print(f"   Contenu brut:\n{content}\n")
            
            json_str = self._extract_json_str(content)
            
            if self.debug:
                print(f"✅ JSON extrait:\n{json_str}\n")
            
            # IMPORTANT: json.loads() convertit automatiquement 
            # false/true/null en False/True/None (Python)
            # Pas besoin de conversion manuelle
            obj = json.loads(json_str)
            print("✅ JSON parsé avec succès (tentative 1)")
            return obj
            
        except json.JSONDecodeError as e:
            print(f"⚠️  JSONDecodeError (tentative 1): {e}")
            print(f"   Position: line {e.lineno}, col {e.colno}")
            print(f"   Extrait problématique: ...{json_str[max(0, e.pos-50):e.pos+50]}...")
        except ValueError as e:
            print(f"⚠️  ValueError (tentative 1): {e}")
            print(f"   Contenu reçu: {content[:500]}")
        except Exception as e:
            print(f"⚠️  Erreur inattendue (tentative 1): {type(e).__name__}: {e}")

        # Repair attempt
        print("\n🔧 Tentative 2/2: réparation JSON...")
        repair_messages = messages + [
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": (
                    "Corrige ta réponse. "
                    "Rends UNIQUEMENT un JSON valide conforme au schéma demandé, "
                    "sans aucun texte autour. Pas de markdown, pas d'explication."
                ),
            },
        ]

        repaired = self._post_chat(repair_messages, temperature=0.0)
        
        if self.debug:
            print(f"🔍 Réponse réparée:\n{repaired}\n")
        
        json_str = self._extract_json_str(repaired)
        
        if self.debug:
            print(f"✅ JSON extrait (réparé):\n{json_str}\n")
        
        obj = json.loads(json_str)
        print("✅ JSON parsé avec succès (tentative 2)")
        return obj