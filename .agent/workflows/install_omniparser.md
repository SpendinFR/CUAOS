---
description: Install OmniParser v2.0 for UI Detection
---

# Installation OmniParser v2.0 (Windows)

Ce workflow installe OmniParser v2.0 de Microsoft pour la détection d'éléments UI avec caption sémantique.

## Prérequis

- Python 3.10+ installé
- Git installé
- Connexion internet pour télécharger les modèles (~500MB)

## Étapes d'installation

### 1. Cloner le repository OmniParser

// turbo
```powershell
cd c:\Users\wabad\Downloads\MUAPPG\MUAG
git clone https://github.com/microsoft/OmniParser.git
```

### 2. Installer les dépendances OmniParser

```powershell
cd OmniParser
pip install -r requirements.txt
```

### 3. Créer le dossier weights

// turbo
```powershell
New-Item -Path "weights" -ItemType Directory -Force
```

### 4. Télécharger les modèles pré-entraînés

**Icon Detection (YOLOv8 Nano)** :
```powershell
huggingface-cli download microsoft/OmniParser-v2.0 "icon_detect/train_args.yaml" --local-dir weights
huggingface-cli download microsoft/OmniParser-v2.0 "icon_detect/model.pt" --local-dir weights
huggingface-cli download microsoft/OmniParser-v2.0 "icon_detect/model.yaml" --local-dir weights
```

**Icon Caption (Florence-2)** :
```powershell
huggingface-cli download microsoft/OmniParser-v2.0 "icon_caption/config.json" --local-dir weights
huggingface-cli download microsoft/OmniParser-v2.0 "icon_caption/generation_config.json" --local-dir weights
huggingface-cli download microsoft/OmniParser-v2.0 "icon_caption/model.safetensors" --local-dir weights
```

### 5. Renommer le dossier icon_caption

// turbo
```powershell
Move-Item -Path "weights\icon_caption" -Destination "weights\icon_caption_florence" -Force
```

### 6. Vérifier l'installation

// turbo
```powershell
cd ..
python -c "import torch; import ultralytics; from transformers import AutoModel; print('✅ Dépendances OK')"
```

## Structure finale attendue

```
MUAPPG/MUAG/
├── OmniParser/
│   └── weights/
│       ├── icon_detect/
│       │   ├── train_args.yaml
│       │   ├── model.pt
│       │   └── model.yaml
│       └── icon_caption_florence/
│           ├── config.json
│           ├── generation_config.json
│           └── model.safetensors
```

## Notes

- Les modèles pèsent environ 500MB au total
- Le téléchargement peut prendre quelques minutes selon votre connexion
- Si `huggingface-cli` n'est pas installé : `pip install huggingface-hub`
