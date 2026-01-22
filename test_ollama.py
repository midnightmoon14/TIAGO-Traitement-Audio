import requests, json

BASE = "http://127.0.0.1:11434"
MODEL = "mistral:latest"

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": (
                "Tu dois répondre UNIQUEMENT avec du JSON valide et rien d'autre.\n"
                "Répond exactement avec: {\"ok\": true}\n"
                "Aucun texte avant/après."
            )
        },
        {"role": "user", "content": "Test"}
    ],
    "stream": False,
    "options": {"temperature": 0}
}

r = requests.post(f"{BASE}/api/chat", json=payload, timeout=120)
r.raise_for_status()
data = r.json()

print("RAW:\n", json.dumps(data, indent=2, ensure_ascii=False))
print("\nCONTENT:\n", data["message"]["content"])

# validation rapide
content = data["message"]["content"].strip()
print("\nPARSED JSON:", json.loads(content))
