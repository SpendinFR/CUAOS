# 📋 Plan d'Installation Complet - MUAG Agent CUA

## 🎯 Vue d'Ensemble

Ce guide vous accompagne **étape par étape** pour installer et configurer l'agent vocal CUA autonome.

**Temps estimé**: 30-45 minutes  
**Espace disque**: ~25GB  
**RAM requise**: 16GB minimum

---

## 📦 Étape 1: Prérequis Système

### Vérifications

| Élément | Requis | Vérification |
|---------|--------|--------------|
| OS | Windows 10/11 | `winver` |
| Python | 3.8-3.11 | `python --version` |
| RAM | 16GB+ | Gestionnaire de tâches |
| Disque | 25GB libre | Explorateur |
| Micro | Oui | Paramètres son |

### Installation Python (si absent)

```bash
# Télécharger Python 3.11
# https://www.python.org/downloads/

# Lors de l'installation:
☑ Add Python to PATH
☑ Install pip

# Vérifier
python --version  # Doit afficher 3.8+
pip --version
```

---

## 🧠 Étape 2: Installer Ollama + Modèles

### 2.1 Installer Ollama

```bash
# 1. Télécharger Ollama
# https://ollama.ai → Download for Windows

# 2. Installer (double-clic .exe)

# 3. Démarrer Ollama
# Icône dans la barre des tâches doit apparaître

# 4. Vérifier
ollama list
# Si fonctionne → OK!
```

### 2.2 Installer le LLM (Qwen2.5)

```bash
# Modèle pour planification et décision
ollama pull qwen2.5:7b-instruct-q4_K_M

# Taille: ~4.7GB
# Temps: 5-10 minutes (selon connexion)

# Vérifier
ollama list
# Doit montrer: qwen2.5:7b-instruct-q4_K_M
```

### 2.3 Installer le VLM (Vision)

```bash
# IMPORTANT: Le VLM est le CŒUR du CUA!

# Option 1: Qwen2-VL 7B (Recommandé)
ollama pull qwen2-vl:7b
# Taille: ~7GB
# Précision: Excellente
# Vitesse: Moyenne

# OU Option 2: Qwen2-VL 2B (Si RAM limitée)
ollama pull qwen2-vl:2b
# Taille: ~2GB
# Précision: Bonne
# Vitesse: Rapide
```

### 2.4 Tester les Modèles

```bash
# Test LLM
ollama run qwen2.5:7b-instruct-q4_K_M "Bonjour"
# Doit répondre en français

# Test VLM (nécessite une image)
# On testera plus tard avec l'agent
```

**✅ Checkpoint**: Vous devez avoir 2 modèles dans `ollama list`

---

## 🐍 Étape 3: Dépendances Python

### 3.1 Naviguer vers le Projet

```bash
cd c:\Users\wabad\Downloads\MUAPPG\MUAG
```

### 3.2 Installation Automatique (Recommandé)

```bash
python setup_models.py
```

Ce script va:
1. ✅ Vérifier Python 3.8+
2. ✅ Créer les dossiers (`data/`, `models/`, etc.)
3. ✅ Installer les dépendances (`requirements.txt`)
4. ✅ Vérifier Ollama
5. ✅ Tester Whisper et TTS (télécharge ~3-4GB)

**Durée**: 10-20 minutes

### 3.3 Installation Manuelle (Alternative)

```bash
# Installer les dépendances
pip install -r requirements.txt

# Packages principaux installés:
# - faster-whisper   (~500MB avec modèle)
# - TTS (Coqui)      (~2GB avec modèle)
# - torch            (~2GB)
# - pyautogui        (~5MB)
# - pyaudio          (~2MB)
# + dépendances...
```

### 3.4 Dépendances Système (Windows)

#### PyAudio (Pour microphone)

Si `pip install pyaudio` échoue:

```bash
# Télécharger le wheel pré-compilé:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

# Exemple pour Python 3.11 64-bit:
pip install PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl
```

#### Tesseract OCR (Optionnel)

```bash
# Télécharger:
# https://github.com/UB-Mannheim/tesseract/wiki

# Installer puis ajouter au PATH:
# C:\Program Files\Tesseract-OCR
```

**✅ Checkpoint**: `pip list` doit montrer tous les packages

---

## 🎤 Étape 4: Configuration Audio

### 4.1 Vérifier le Microphone

```bash
# Windows: Paramètres → Son → Entrée
# Parlez et vérifiez que la barre bouge

# Python test:
python -c "from voice.audio_handler import AudioHandler; AudioHandler().list_devices()"
```

### 4.2 Calibration (Important!)

Au premier lancement de `main.py`, l'agent va:
1. Demander de **rester silencieux** 3 secondes (calibre seuil bruit)
2. Demander de **parler** pour tester

**Si la détection ne fonctionne pas**:

Éditez `config.py`:
```python
# Augmenter si trop sensible (capte bruit ambiant)
AUDIO_SILENCE_THRESHOLD = 800  # Défaut: 500

# Augmenter si agent coupe trop vite
AUDIO_SILENCE_DURATION = 2.0  # Défaut: 1.5
```

---

## 🧪 Étape 5: Tests de Validation

### 5.1 Test Mode Texte (Sans voix)

```bash
python main.py --text
```

Tapez: `Bonjour`

**Attendu**:
```
🔍 Analyse de: Bonjour
💡 Intention détectée: CONVERSATION
💬 Mode: CONVERSATION
💬 Assistant: Bonjour! Je vais très bien, merci. Comment puis-je vous aider?
```

**✅ Si ça fonctionne**: L'IA et la mémoire marchent!

### 5.2 Test Action Simple

```bash
python main.py --text
```

Tapez: `Ouvre la calculatrice`

**Attendu**:
```
🎬 Mode: ACTION
📝 Plan: ...
✅ TERMINÉ
```

La calculatrice doit s'ouvrir!

**✅ Si ça fonctionne**: L'executeur marche!

### 5.3 Test Voice (Vocal)

```bash
python main.py
```

1. Calibration micro (rester silencieux)
2. Agent dit: "Bonjour! Je suis Assistant..."
3. **Parlez**: "Bonjour"
4. Agent devrait répondre vocalement

**✅ Si ça fonctionne**: Voice complète marche!

### 5.4 Test CUA (Vision-Action)

```bash
python tests/test_cua.py
```

Menu:
```
1. Test simple (ouvrir bloc-notes)
2. Test web (recherche Google)
3. Test complexe (Amazon)
```

Choisissez **1** (Test simple)

**Attendu**:
```
Étape 1:
👁️ Vision: Bureau Windows...
🧠 Action: launch_app("notepad")
✅ Résultat: Application lancée

✅ Tâche terminée en 3 étapes!
```

**✅ Si ça fonctionne**: CUA complet marche!

---

## 📝 Étape 6: Configuration Personnalisée

### 6.1 Fichiers de Configuration

Éditez `config.py` selon vos besoins:

```python
# === VOICE ===
WHISPER_MODEL = "medium"      # ou "base" si RAM faible
TTS_LANGUAGE = "fr"           # ou "en" pour anglais
AUDIO_SILENCE_THRESHOLD = 500 # Ajuster si besoin

# === CUA ===
TARS_MODEL_NAME = "qwen2-vl:7b"  # VLM principal
FALLBACK_VLM_MODEL = "qwen2-vl:7b"

# === SECURITY ===
REQUIRE_CONFIRMATION_PURCHASE = True
REQUIRE_CONFIRMATION_EMAIL = True
MAX_AUTO_PURCHASE_AMOUNT = 0  # Toujours confirmer

# === AGENT ===
AGENT_NAME = "Assistant"  # Personnalisez!
AGENT_PERSONALITY = "helpful"  # ou "friendly", "professional"
```

### 6.2 Fichiers de Données

Les fichiers sont créés automatiquement dans `data/`:
- `memory.json`: Historique conversations
- `preferences.json`: Préférences utilisateur
- `skills.json`: Compétences apprises
- `screenshots/`: Screenshots CUA

---

## 🎯 Étape 7: Utilisation Quotidienne

### Démarrer l'Agent

```bash
# Mode vocal (usage normal)
python main.py

# Mode texte (debugging)
python main.py --text
```

### Exemples de Tâches

**Niveau 1 - Simple**:
```
"Ouvre Chrome"
"Lance la calculatrice"
"Quelle heure est-il?"
```

**Niveau 2 - Moyen**:
```
"Cherche la météo à Paris"
"Crée un fichier test.txt sur le bureau"
"Trouve un restaurant italien à Lyon"
```

**Niveau 3 - Complexe (CUA)**:
```
"Commande des écouteurs sans fil sur Amazon"
"Envoie un email à john@example.com sujet Réunion"
"Réserve un billet de train Paris-Lyon demain"
```

L'agent détecte automatiquement le niveau et active CUA si nécessaire!

---

## ❓ FAQ & Dépannage

### Q: L'agent ne me comprend pas (STT)

**Solutions**:
1. Parlez plus fort
2. Réduisez le bruit ambiant
3. Utilisez un meilleur micro
4. Changez modèle: `WHISPER_MODEL = "large-v2"`

### Q: L'agent clique au mauvais endroit (CUA)

**Normal!** Sans Object Detection précis, le VLM estime les coordonnées.

**Solutions**:
1. Utilisez VLM plus grand: `ollama pull qwen2-vl:14b`
2. Attendez la v1.1 (Object Detection intégré)
3. Ajoutez délais: `CUA_STEP_DELAY = 2`

### Q: "Erreur mémoire" lors du lancement

**Trop de modèles en RAM**:
1. Fermez autres applications
2. Utilisez modèles plus légers:
   - `WHISPER_MODEL = "base"`
   - `ollama pull qwen2-vl:2b`

### Q: CAPTCHA bloque l'agent

**Normal!** L'agent ne peut pas résoudre les CAPTCHA.

**Solutions**:
1. Sites sans CAPTCHA
2. Se connecter manuellement avant
3. Future v1.2: intégration 2Captcha

### Q: L'agent est lent

**Vision + LLM prend du temps** (2-5 sec/action)

**Solutions**:
1. Utilisez GPU (accélère x3-5)
2. Modèles plus légers
3. Attendez - c'est normal pour autonomie

---

## 📊 Récapitulatif Installation

### Checklist Complète

- [ ] Python 3.8-3.11 installé
- [ ] Ollama installé et démarré
- [ ] Qwen2.5 LLM téléchargé (`ollama list`)
- [ ] Qwen2-VL VLM téléchargé (`ollama list`)
- [ ] Dependencies Python installées (`pip list`)
- [ ] PyAudio fonctionne (micro détecté)
- [ ] Test mode texte OK (`python main.py --text`)
- [ ] Test vocal OK (`python main.py`)
- [ ] Test CUA OK (`python tests/test_cua.py`)

### Espace Disque Utilisé

- Ollama modèles: ~12GB
- Whisper modèle: ~1.5GB
- XTTS modèle: ~2GB
- Python packages: ~3GB
- **Total**: ~18-20GB

### Configuration Minimale vs Recommandée

| Composant | Minimal | Recommandé |
|-----------|---------|------------|
| RAM | 12GB | 16-32GB |
| CPU | 4 cores | 8+ cores |
| GPU | Aucun | NVIDIA 4GB+ VRAM |
| Disque | 20GB | 50GB+ |
| Internet | 10 Mbps | 50+ Mbps |

---

## 🎊 Félicitations!

Si vous êtes arrivé ici et que tous les tests passent, vous avez maintenant un **agent vocal CUA autonome complet** capable de:

✅ Comprendre votre voix  
✅ Décider intelligemment  
✅ Voir l'écran  
✅ Exécuter N'IMPORTE QUELLE tâche  
✅ Apprendre et mémoriser  

**Prochaines étapes**:
1. Explorez avec des tâches simples
2. Progressez vers des tâches complexes
3. Consultez [CUA_GUIDE.md](file:///c:/Users/wabad/Downloads/MUAPPG/MUAG/CUA_GUIDE.md) pour avancé
4. Personnalisez `config.py` à votre guise

---

**Besoin d'aide?** Relisez les sections pertinentes ou consultez les guides!

Bon agent autonome! 🚀
