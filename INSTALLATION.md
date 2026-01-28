# 📦 Guide d'Installation - TIAGO Assistant Vocal

## Prérequis

- **Python 3.12+** (recommandé) ou Python 3.10+
- **Windows 10/11** (ou Linux/macOS)
- **8 GB RAM minimum** (16 GB recommandé pour Ollama)
- **Connexion internet** (pour télécharger les modèles et Google TTS)

---

## Étape 1 : Installer Python

### Windows
1. Téléchargez Python depuis https://www.python.org/downloads/
2. **IMPORTANT** : Cochez "Add Python to PATH" lors de l'installation
3. Vérifiez l'installation :
```bash
python --version
# Doit afficher Python 3.10 ou supérieur
```

### Linux/macOS
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip

# macOS (avec Homebrew)
brew install python3
```

---

## Étape 2 : Installer les dépendances Python

### Option A : Installation automatique (recommandé)
```bash
# Depuis le dossier du projet
pip install -r requirements.txt
```

### Option B : Installation manuelle
```bash
pip install requests>=2.31.0
pip install faster-whisper>=1.0.0
pip install numpy>=1.24.0
pip install pyaudio>=0.2.11
pip install gtts>=2.5.0
```

### ⚠️ Problème avec PyAudio sur Windows ?

Si `pip install pyaudio` échoue :

**Solution 1 : Utiliser pipwin**
```bash
pip install pipwin
pipwin install pyaudio
```

**Solution 2 : Télécharger le wheel**
1. Allez sur https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Téléchargez le fichier correspondant à votre version Python (ex: `PyAudio-0.2.11-cp312-cp312-win_amd64.whl`)
3. Installez-le :
```bash
pip install PyAudio-0.2.11-cp312-cp312-win_amd64.whl
```

---

## Étape 3 : Installer Ollama

Ollama est **requis** pour le LLM local. Il ne s'installe pas via pip.

### Windows
```bash
# Méthode 1 : Winget (recommandé)
winget install Ollama.Ollama

# Méthode 2 : Téléchargement manuel
# Allez sur https://ollama.com/download
# Téléchargez et installez Ollama pour Windows
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS
```bash
# Méthode 1 : Homebrew
brew install ollama

# Méthode 2 : Téléchargement manuel
# Allez sur https://ollama.com/download
```

### Vérifier l'installation
```bash
ollama --version
# Doit afficher la version d'Ollama
```

### Démarrer Ollama
```bash
# Windows : Ollama démarre automatiquement après l'installation
# Si ce n'est pas le cas :
ollama serve

# Linux/macOS :
ollama serve
```

Ollama tourne sur `http://127.0.0.1:11434` par défaut.

---

## Étape 4 : Télécharger un modèle Ollama

Vous devez télécharger au moins un modèle pour que le système fonctionne.

### Modèles recommandés (par ordre de vitesse)

**1. Modèle rapide (recommandé pour débuter) :**
```bash
ollama pull llama3.2:3b
```

**2. Modèle équilibré (bon compromis) :**
```bash
ollama pull llama3.1:8b-q4_K_M
# Version quantifiée, 2x plus rapide que la version normale
```

**3. Modèle complet (meilleure qualité, plus lent) :**
```bash
ollama pull llama3.1:8b
```

**4. Modèle très léger (le plus rapide) :**
```bash
ollama pull qwen2:1.5b
```

### Vérifier les modèles installés
```bash
ollama list
```

### Changer de modèle dans le code
Modifiez `main.py` ligne 43 :
```python
llm = OllamaClient(base_url="http://127.0.0.1:11434", model="llama3.2:3b")
```

---

## Étape 5 : Vérifier l'installation

### Test rapide
```bash
# Test Python
python --version

# Test Ollama
ollama list

# Test des dépendances Python
python -c "import requests, numpy, faster_whisper, pyaudio; print('✅ Toutes les dépendances sont installées')"
```

### Test complet du projet
```bash
python main.py
```

Si tout fonctionne, vous devriez voir :
```
============================================================
🤖 TIAGO - Assistant vocal CESI
============================================================
🔧 Chargement du modèle Whisper...
🔧 Calibration micro (2 secondes)...
✅ TIAGO est prêt !
```

---

## Dépannage

### Ollama ne démarre pas
```bash
# Windows : Vérifiez dans le Gestionnaire des tâches
# Linux/macOS : Vérifiez les processus
ps aux | grep ollama

# Redémarrer Ollama
ollama serve
```

### Erreur "Module not found"
```bash
# Réinstaller toutes les dépendances
pip install --upgrade -r requirements.txt
```

### Microphone non détecté
1. **Windows** : Paramètres → Son → Entrée → Testez votre micro
2. Vérifiez que le micro n'est pas utilisé par une autre application
3. Listez les micros disponibles :
```bash
python -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"
```

### Modèle Ollama trop lent
- Utilisez une version quantifiée : `llama3.1:8b-q4_K_M`
- Ou un modèle plus petit : `llama3.2:3b`
- Vérifiez vos ressources CPU/RAM

---

## Structure des fichiers après installation

```
tiag/
├── main.py
├── requirements.txt          ← Ce fichier
├── INSTALLATION.md           ← Ce guide
├── tiago_assistant/
│   ├── __init__.py
│   ├── stt.py
│   ├── ollama_client.py
│   ├── prompts.py
│   ├── validator.py
│   └── ...
└── models/                   ← Modèles Whisper (téléchargés automatiquement)
    └── ...
```

---

## Mise à jour

### Mettre à jour les dépendances Python
```bash
pip install --upgrade -r requirements.txt
```

### Mettre à jour Ollama
```bash
# Windows : Réinstaller via winget
winget upgrade Ollama.Ollama

# Linux/macOS : Suivre les instructions sur https://ollama.com
```

### Mettre à jour un modèle Ollama
```bash
ollama pull llama3.2:3b  # Re-télécharge la dernière version
```

---

## Support

En cas de problème :
1. Vérifiez que tous les prérequis sont installés
2. Consultez la section Dépannage ci-dessus
3. Vérifiez les logs dans le terminal
4. Consultez la documentation : `DOCUMENTATION.md`
