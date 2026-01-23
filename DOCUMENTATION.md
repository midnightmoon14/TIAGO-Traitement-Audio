# Documentation du Projet TIAGO

## Fichiers principaux (core)

### `main.py` — Point d'entrée principal
- **Rôle** : Orchestre tout le système
- **Fonctions** :
  - Détecte le wake word "Bonjour Tiago"
  - Gère la boucle de conversation : écoute → traitement LLM → réponse vocale
  - Limite la longueur des réponses (220 caractères max)
  - Affiche les messages de debug
- **Dépendances** : Utilise `stt.py`, `tts.py`, `ollama_client.py`, `prompts.py`, `validator.py`

### `stt.py` — Speech-to-Text (reconnaissance vocale)
- **Rôle** : Convertit la voix en texte
- **Technologie** : Utilise Whisper (faster-whisper)
- **Fonctionnalités** :
  - Enregistre l'audio du micro via PyAudio
  - Vérifie le volume (seuil à 400 pour éviter les faux positifs)
  - Transcrit en français uniquement (langue forcée)
  - Filtre agressivement les hallucinations (caractères asiatiques, probabilités faibles, etc.)
- **Classe** : `STT` avec méthode `listen()`

### `tts.py` — Text-to-Speech (synthèse vocale)
- **Rôle** : Convertit le texte en parole
- **Technologie** : Utilise pyttsx3 (moteur TTS local)
- **Fonctionnalités** :
  - Vitesse de parole configurable (175 mots/min par défaut)
  - Parole en français
- **Classe** : `TTS` avec méthode `say()`

### `ollama_client.py` — Client pour Ollama
- **Rôle** : Communication avec le modèle LLM Ollama
- **Fonctionnalités** :
  - Envoie les messages au modèle Mistral via API HTTP
  - Extrait le JSON de la réponse (même si entouré de texte)
  - Tente une réparation automatique si le JSON est invalide
- **Classe** : `OllamaClient` avec méthode `chat_json()`

### `prompts.py` — Prompt système
- **Rôle** : Définit le comportement de Tiago
- **Contenu** : `SYSTEM_PROMPT` qui contient :
  - Instructions pour le robot guide CESI Bordeaux
  - Règles de conversation
  - Format JSON attendu en réponse
  - Catégories de formations (rouge, bleu, vert, jaune)

### `validator.py` — Validation des réponses
- **Rôle** : Vérifie la structure et la validité des réponses JSON
- **Fonctionnalités** :
  - Vérifie les clés requises (`say`, `done`, `ask_confirmation`, etc.)
  - Valide les couleurs autorisées (rouge, bleu, vert, jaune)
  - Valide les labels de formations
  - Assure la cohérence des données (ex: `done=true` nécessite `dataset`)
- **Fonction** : `validate(obj)`

## Fichiers de test/debug

### `test_ollama.py` — Test Ollama
- **Rôle** : Vérifie la connexion à Ollama
- **Usage** : Teste si le modèle répond en JSON valide
- **Commande** : `python test_ollama.py`

### `test_stt_volume.py` — Test du volume du micro
- **Rôle** : Aide à calibrer le seuil de volume
- **Fonctionnalités** :
  - Affiche le volume détecté en temps réel
  - Barre de volume visuelle
  - Aide à déterminer le bon `volume_threshold` dans `stt.py`
- **Commande** : `python test_stt_volume.py`

### `test_wake_word.py` — Test du wake word
- **Rôle** : Teste la détection du wake word
- **Fonctionnalités** :
  - Teste la fonction `is_wake()` avec différents textes
  - Teste la détection du wake word avec le micro réel
- **Commande** : `python test_wake_word.py`

### `list_audio_devices.py` — Liste des périphériques audio
- **Rôle** : Aide à identifier les périphériques audio
- **Fonctionnalités** :
  - Affiche tous les périphériques audio disponibles
  - Affiche le périphérique par défaut
- **Commande** : `python list_audio_devices.py`

## Fichiers système (non modifiables)

### `__pycache__/` — Cache Python
- **Rôle** : Fichiers compilés Python (.pyc) générés automatiquement
- **Note** : Ne pas modifier, généré automatiquement par Python

### `ffmpeg.exe` — Exécutable externe
- **Rôle** : Utilisé par certaines bibliothèques audio
- **Note** : Exclu de Git (dans `.gitignore`)

## Flux du programme

```
1. main.py démarre
   ↓
2. Initialise STT, TTS, OllamaClient
   ↓
3. Mode veille : stt.py écoute en continu
   ↓
4. Détection wake word : main.py vérifie "Bonjour Tiago"
   ↓
5. Conversation :
   - stt.py écoute la voix
   - ollama_client.py envoie à Ollama
   - validator.py valide la réponse
   - tts.py parle la réponse
   ↓
6. Retour au mode veille (étape 3)
```

## Dépendances principales

- **faster-whisper** : Reconnaissance vocale (STT)
- **pyttsx3** : Synthèse vocale (TTS)
- **pyaudio** : Capture audio du micro
- **requests** : Communication HTTP avec Ollama
- **numpy** : Traitement des données audio

## Configuration

- **Modèle Whisper** : `small` (peut être changé dans `main.py`)
- **Modèle Ollama** : `mistral:latest` (peut être changé dans `main.py`)
- **Seuil de volume** : `400` (peut être ajusté dans `stt.py`)
- **Vitesse TTS** : `175` mots/min (peut être ajusté dans `main.py`)
