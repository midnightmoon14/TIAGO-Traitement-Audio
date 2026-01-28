# 🤖 TIAGO - Assistant Vocal JPO CESI Bordeaux

Documentation complète du projet - Version Janvier 2025

---

## 📋 TABLE DES MATIÈRES

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du système](#architecture-du-système)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Utilisation](#utilisation)
6. [Structure des fichiers](#structure-des-fichiers)
7. [API et Intégration](#api-et-intégration)
8. [Dépannage](#dépannage)
9. [Spécifications techniques](#spécifications-techniques)

---

## 🎯 VUE D'ENSEMBLE

### Objectif
TIAGO est un assistant vocal intelligent pour la Journée Portes Ouvertes du CESI Bordeaux. Il guide les visiteurs vers la formation la plus adaptée à leur profil.

### Fonctionnalités
- ✅ **Détection vocale** (wake word : "Bonjour Tiago")
- ✅ **Conversation naturelle** en français et anglais
- ✅ **Recommandation intelligente** de formations
- ✅ **Synthèse vocale** de qualité (Google TTS)
- ✅ **Dataset final** avec couleur de brochure

### Les 4 formations CESI
| Formation | Couleur | Public | Objectif |
|-----------|---------|--------|----------|
| **Programme Grande Ecole** | 🟡 JAUNE | Lycéens/Bac+2/3 | Diplôme ingénieur Bac+5 |
| **Bachelor De Specialite** | 🔵 BLEU | Lycéens | Bac+3 professionnel |
| **Master Professionnel** | 🔴 ROUGE | Bac+3/4 | Spécialisation Bac+5 |
| **Programme Executive** | 🟢 VERT | Professionnels | Formation continue |

---

## 🏗️ ARCHITECTURE DU SYSTÈME

### Pipeline complet

```
┌─────────────────────────────────────────────────────────────┐
│  1. WAKE WORD DETECTION                                     │
│     Écoute continue → "Bonjour Tiago" détecté              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  2. SPEECH-TO-TEXT (STT)                                    │
│     Audio → Whisper (faster-whisper) → Texte français      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  3. LANGUAGE MODEL (LLM)                                    │
│     Texte → Ollama (local) → JSON structuré                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  4. TEXT-TO-SPEECH (TTS)                                    │
│     Texte → Google TTS → Audio                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  5. OUTPUT JSON                                             │
│     {"couleur": "jaune", "quantite": 1} → Action robot     │
└─────────────────────────────────────────────────────────────┘
```

### Composants principaux

| Composant | Technologie | Rôle |
|-----------|------------|------|
| **STT** | Faster Whisper (small) | Transcription audio → texte |
| **LLM** | Ollama (llama3.2:3b ou phi3:mini) | Intelligence conversationnelle locale |
| **TTS** | Google Text-to-Speech | Synthèse vocale naturelle |
| **Validation** | Python JSON Schema | Vérification format de sortie |

---

## 💻 INSTALLATION

### Prérequis
- **Python 3.12+**
- **Windows 10/11** (ou Linux/macOS)
- **8 GB RAM minimum** (16 GB recommandé pour Ollama)
- **Connexion internet** (pour Google TTS uniquement)

### Étape 1 : Cloner le projet
```bash
git clone <votre-repo>
cd tiag
```

### Étape 2 : Installer les dépendances
```bash
pip install -r requirements.txt
```

**Contenu de `requirements.txt` :**
```
faster-whisper
pyaudio
numpy
gtts
pygame
requests
```

### Étape 3 : Installer Ollama (requis pour LLM local)
```bash
# Windows
winget install Ollama.Ollama

# Télécharger un modèle léger et rapide (recommandé)
ollama pull llama3.2:3b

# Ou alternatives :
# ollama pull phi3:mini      # Excellent en français
# ollama pull qwen2:1.5b     # Le plus léger
```

---

## ⚙️ CONFIGURATION

### Configuration du micro

**1. Lister les micros disponibles :**
```bash
python list_audio_devices.py
```

**2. Configurer dans `main.py` :**
```python
MICRO_INDEX = 1  # Changez selon votre micro
stt = STT(
    model_size="small",
    device="cpu",
    compute_type="int8",
    input_device_index=MICRO_INDEX
)
```

### Configuration du LLM

**Ollama local (illimité, ~5-15s/réponse selon modèle) :**
```python
from tiago_assistant.ollama_client import OllamaClient

# Modèle recommandé : llama3.2:3b (équilibre vitesse/qualité)
llm = OllamaClient(
    base_url="http://127.0.0.1:11434",
    model="llama3.2:3b"
)

# Alternatives :
# model="phi3:mini"      # Excellent en français
# model="qwen2:1.5b"     # Le plus léger et rapide
```

### Paramètres ajustables

| Paramètre | Fichier | Ligne | Description |
|-----------|---------|-------|-------------|
| Durée écoute | `main.py` | ~110 | `seconds=5.0` (timeout écoute) |
| Seuil volume | `stt.py` | ~70 | `volume_threshold` (sensibilité micro) |
| Wake word | `main.py` | ~30 | Fonction `is_wake()` |
| Température LLM | `main.py` | ~125 | `temperature=0.2` (créativité) |
| Vitesse TTS | N/A | N/A | Google TTS = vitesse fixe |

---

## 🚀 UTILISATION

### Lancement basique
```bash
python main.py
```

### Flux d'interaction

**1. Démarrage :**
```
🔧 Calibration du micro (2 secondes de silence)
✅ TIAGO prêt !
🎤 En attente du wake word...
```

**2. Activation :**
```
Vous : "Bonjour Tiago"
✅ Wake word détecté !
Tiago : "Bonjour ! Comment je peux vous aider ?"
```

**3. Conversation :**
```
Vous : "Je cherche une formation en informatique"
Tiago : "Super ! Quel est votre niveau : lycée, bac+2 ou bac+3 ?"

Vous : "Je suis en terminale"
Tiago : "Parfait ! Vous visez ingénieur ou bac+3 ?"

Vous : "Ingénieur"
Tiago : "Le Programme Grande École est idéal pour vous. Intéressé ?"

Vous : "Oui"
Tiago : "Génial ! Bonne visite au CESI Bordeaux."
📊 DATASET FINAL : {"couleur": "jaune", "quantite": 1}
```

### Arrêt
- Appuyez sur `Ctrl+C` pour arrêter proprement

---

## 📁 STRUCTURE DES FICHIERS

```
tiag/
├── main.py                     # Orchestration principale
├── stt.py                      # Speech-to-Text (Whisper)
├── tts_gtts.py                 # Text-to-Speech (Google)
├── prompts.py                  # Prompt système LLM
├── validator.py                # Validation JSON
├── ollama_client.py            # Client Ollama (local uniquement)
├── list_audio_devices.py       # Utilitaire liste micros
├── requirements.txt            # Dépendances Python
├── DOCUMENTATION.md            # Ce fichier
└── .gitignore                  # Fichiers ignorés par Git
```

### Description des fichiers

#### `main.py`
Fichier principal qui orchestre :
- Calibration du micro
- Détection wake word
- Boucle de conversation
- Gestion historique
- Validation et output final

#### `stt.py`
Classe `STT` pour la transcription audio :
- Initialisation Whisper (faster-whisper)
- Calibration automatique du seuil de volume
- Filtrage VAD (Voice Activity Detection)
- Nettoyage transcriptions (pas de langue asiatique, etc.)

#### `tts_gtts.py`
Classe `TTS` pour la synthèse vocale :
- Google Text-to-Speech (gTTS)
- Détection automatique français/anglais
- Lecture audio avec pygame
- Correction prononciation ("CESI" → "Saisie")

#### `prompts.py`
Prompt système pour le LLM :
- Description des 4 formations
- Arbre de décision
- Format JSON strict
- Exemples de conversations
- Règles conversationnelles

#### `validator.py`
Validation du JSON retourné par le LLM :
- Vérification des champs obligatoires
- Validation couleurs/labels autorisés
- Cohérence done/dataset/proposed

#### `ollama_client.py`
Client pour Ollama (LLM local) :
- Communication avec serveur local
- Extraction et nettoyage JSON
- Tentative de réparation si JSON invalide
- Debug et logs

---

## 🔌 API ET INTÉGRATION

### Pour intégrer au robot

Le robot appelle votre code comme un **module Python** :

```python
# robot_main.py (code du robot)
from main import TiagoAssistant  # À créer

tiago = TiagoAssistant()

# Démarrer conversation
response = tiago.start_conversation()
robot.speak(response['say'])

# Boucle conversation
while True:
    audio = robot.record_audio(seconds=5)
    response = tiago.process_turn(audio)
    
    robot.speak(response['say'])
    
    if response['done']:
        couleur = response['dataset']['couleur']
        robot.take_brochure(couleur)
        break
```

### Format JSON de sortie

**Structure complète :**
```json
{
  "say": "Texte que le robot doit dire (max 25 mots)",
  "done": false,
  "ask_confirmation": false,
  "proposed": null,
  "dataset": null,
  "handoff": false
}
```

**Quand une formation est proposée :**
```json
{
  "say": "Le Programme Grande École est parfait pour vous. Intéressé ?",
  "done": false,
  "ask_confirmation": true,
  "proposed": {
    "label": "Programme Grande Ecole",
    "couleur": "jaune"
  },
  "dataset": null,
  "handoff": false
}
```

**Quand conversation terminée (dataset final) :**
```json
{
  "say": "Génial ! Bonne visite au CESI Bordeaux.",
  "done": true,
  "ask_confirmation": false,
  "proposed": {
    "label": "Programme Grande Ecole",
    "couleur": "jaune"
  },
  "dataset": {
    "couleur": "jaune",
    "quantite": 1
  },
  "handoff": false
}
```

**Quand question hors sujet :**
```json
{
  "say": "Je ne connais pas les tarifs. L'équipe vous renseignera !",
  "done": false,
  "ask_confirmation": false,
  "proposed": null,
  "dataset": null,
  "handoff": true
}
```

---

## 🔧 DÉPANNAGE

### Problème : Calibration à 0

**Symptôme :**
```
📊 Bruit ambiant: 0
🎯 Seuil de détection: 1
```

**Causes possibles :**
- Micro non branché
- Micro désactivé dans Windows
- Mauvais index de micro

**Solutions :**
1. Vérifiez : Paramètres Windows → Son → Entrée
2. Testez le micro (la barre doit bouger quand vous parlez)
3. Listez les micros : `python list_audio_devices.py`
4. Changez `MICRO_INDEX` dans `main.py`

---

### Problème : LLM ne répond pas en JSON

**Symptôme :**
```
⚠️  ValueError: No JSON found in model output
```

**Causes :**
- Prompt trop long (Mistral 7B se perd)
- Modèle ne comprend pas les instructions
- Température trop élevée

**Solutions :**
1. Utilisez un modèle plus récent : `llama3.2:3b` ou `phi3:mini`
2. Réduisez la température : `temperature=0.1`
3. Simplifiez le prompt (déjà optimisé dans `prompts.py`)
4. Vérifiez qu'Ollama est bien démarré : `ollama serve`

---

---

### Problème : TTS n'a pas de voix française

**Symptôme :**
```
⚠️  Aucune voix française trouvée
```

**Solution (tts_gtts.py - déjà en place) :**
Google TTS utilise automatiquement une voix française de qualité. Pas besoin de configuration.

---

### Problème : PyAudio installation failed

**Symptôme :**
```
ERROR: Could not build wheels for pyaudio
```

**Solution Windows :**
```bash
pip install pipwin
pipwin install pyaudio
```

**Solution alternative :**
Téléchargez le wheel : https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
```bash
pip install PyAudio‑0.2.11‑cp312‑cp312‑win_amd64.whl
```

---

## 📊 SPÉCIFICATIONS TECHNIQUES

### Performance

| Métrique | Valeur | Notes |
|----------|--------|-------|
| **Latence STT** | 1-2s | Whisper small sur CPU |
| **Latence LLM (Ollama)** | 5-15s | Local, dépend du modèle et CPU |
| **Latence TTS** | 1-2s | Google TTS + pygame |
| **Latence totale** | 8-20s | Par tour de parole |


### Limitations

| Limite | Valeur | Contournement |
|--------|--------|---------------|
| **Requêtes Ollama** | Illimitées | Local uniquement |
| **Durée écoute max** | 5s | Ajustable dans code |
| **Langues supportées** | FR, EN | Extensible (prompt) |
| **Wake words** | "Bonjour/Hey Tiago" | Modifiable (`is_wake()`) |

### Modèles utilisés

| Composant | Modèle | Taille | Notes |
|-----------|--------|--------|-------|
| **STT** | Whisper Small | 244 MB | Bon compromis vitesse/qualité |
| **LLM (Ollama)** | llama3.2:3b | ~2 GB | Recommandé : rapide et bon en français |
| **LLM (Ollama)** | phi3:mini | ~2.3 GB | Alternative : excellent en français |
| **LLM (Ollama)** | qwen2:1.5b | ~1 GB | Le plus léger et rapide |
| **TTS** | Google TTS | Cloud | Voix naturelle FR/EN |

---

## 📝 NOTES IMPORTANTES

### Prononciation "CESI"
Le système remplace automatiquement "CESI" par "Saisie" pour une prononciation correcte en français.

### Gestion conversation
- Une conversation = 1 visiteur
- Historique conservé pendant la conversation
- Reset automatique après `done: true`

### Sécurité
- Pas de stockage des conversations
- Pas de données personnelles collectées
- Clés API à garder secrètes (`.gitignore`)

### Maintenance
- Mise à jour Ollama : `ollama pull llama3.2:3b`
- Mise à jour dépendances : `pip install -U -r requirements.txt`
- Logs en temps réel dans le terminal
- Vérifier qu'Ollama tourne : `ollama list`

---





{
    "say": "Super ! Vous visez ingénieur ou bac+3 ?",  ← TEXTE pour le TTS
    "done": False,                                      ← Conversation finie ?
    "ask_confirmation": False,
    "proposed": None,
    "dataset": None,                                    ← Brochure (si done=True)
    "handoff": False
}



