# 🚀 Installation de TARS UI pour l'Agent CUA

## Qu'est-ce que TARS UI?

**TARS UI** (ByteDance) est un modèle Vision-Language **spécialisé pour Computer Use**.  
C'est le cœur de votre agent CUA - il "voit" et "comprend" l'écran comme un humain.

## 📥 Installation

### Option 1: Via Ollama (Recommandé)

```bash
# IMPORTANT: TARS UI n'est pas encore dans Ollama officiel
# On utilise donc un VLM alternatif en attendant

# Alternative 1: Qwen2-VL (Excellent pour Computer Use)
ollama pull qwen2-vl:7b

# Alternative 2: LLaVA (Plus léger)
ollama pull llava:7b

# Alternative 3: Qwen2-VL 2B (Si RAM limitée)
ollama pull qwen2-vl:2b
```

### Option 2: TARS UI via HuggingFace (Avancé)

Si vous voulez le vrai TARS UI:

```bash
# 1. Installer transformers
pip install transformers torch

# 2. Le modèle sera téléchargé automatiquement
# Chemin HuggingFace: ByteDance/TARS-UI-1.5-7B
```

Puis modifiez `config.py`:
```python
TARS_MODEL_NAME = "ByteDance/TARS-UI-1.5-7B"  # Via HuggingFace
```

## ✅ Vérification

```bash
# Tester que le VLM fonctionne
ollama run qwen2-vl:7b "Décris ce que tu vois"
```

## 🎯 Configuration dans config.py

```python
# Modèle TARS/VLM à utiliser
TARS_MODEL_NAME = "qwen2-vl:7b"  # ou "llava:7b"

# Fallback si TARS indisponible
FALLBACK_VLM_MODEL = "qwen2-vl:7b"
```

## 📊 Comparaison des Modèles

| Modèle | Taille | RAM | Précision | Vitesse |
|--------|--------|-----|-----------|---------|
| **Qwen2-VL 7B** | ~7GB | 12GB+ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **LLaVA 7B** | ~4GB | 8GB+ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Qwen2-VL 2B** | ~2GB | 6GB+ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **TARS UI (HF)** | ~15GB | 20GB+ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

### Recommandation

Pour la plupart des usages: **Qwen2-VL 7B**
- Excellent équilibre performance/vitesse
- Spécifiquement entraîné pour vision de UI
- Supporte bien le français

## 🧪 Test Rapide

```bash
cd c:\Users\wabad\Downloads\MUAPPG\MUAG
python tests/test_cua.py
```

Choisissez "Test simple" pour vérifier que tout fonctionne.

## ⚠️ Problèmes Courants

### "Modèle non trouvé"
```bash
# Lister les modèles installés
ollama list

# Si absent, installer
ollama pull qwen2-vl:7b
```

### "Erreur de mémoire"
- Utilisez un modèle plus léger: `qwen2-vl:2b` ou `llava:7b`
- Fermez les autres applications
- Minimum 8GB RAM recommandé

### "Vision imprécise"
- Utilisez Qwen2-VL 7B ou plus
- Augmentez la résolution des screenshots
- Ajoutez plus de contexte dans les prompts

## 🎓 Utilisation Avancée

### Personnaliser le VLM

Dans `actions/cua_agent.py`:

```python
# Utiliser un modèle spécifique
agent = CUAAgent(vlm_model="llava:13b")

# Ou laisser auto-detect
agent = CUAAgent()  # Utilise TARS_MODEL_NAME du config
```

### Optimiser la Vitesse

Dans `config.py`:
```python
# Réduire la qualité pour plus de vitesse
TARS_MODEL_NAME = "qwen2-vl:2b"  # Plus rapide

# Augmenter le délai entre étapes
CUA_STEP_DELAY = 2  # Secondes
```

## 📚 Resources

- **Qwen2-VL**: https://github.com/QwenLM/Qwen2-VL
- **LLaVA**: https://github.com/haotian-liu/LLaVA
- **TARS UI**: https://huggingface.co/ByteDance/TARS-UI-1.5-7B
- **Ollama**: https://ollama.ai

---

Une fois installé, votre agent CUA peut accomplir **N'IMPORTE QUELLE TÂCHE**! 🚀
