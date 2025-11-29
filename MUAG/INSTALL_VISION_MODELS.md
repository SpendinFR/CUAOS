# Guide d'Installation - Modèles de Vision CUA

Ce guide vous explique comment installer et configurer les modèles de vision pour le CUA Agent.

## 📦 Installation des Dépendances Python

```bash
# Installer toutes les dépendances
pip install -r requirements.txt
```

### Notes Importantes

#### PaddleOCR
- **PaddlePaddle** s'installe automatiquement
- Téléchargement des modèles OCR au premier lancement (~200MB)
- GPU recommandé mais optionnel

#### YOLOv11
- **Ultralytics** télécharge automatiquement le modèle au premier lancement
- `yolov11m.pt` (~50MB) - Medium model (bon compromis vitesse/précision)
- Alternatives:
  - `yolov11n.pt` (plus rapide, moins précis)
  - `yolov11l.pt` ou `yolov11x.pt` (plus lent, plus précis)

## 🧪 Test de Configuration

```python
# Test PaddleOCR
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='fr', use_gpu=False)
print("✅ PaddleOCR OK")

# Test YOLOv11
from ultralytics import YOLO
model = YOLO('yolov11m.pt')
print("✅ YOLOv11 OK")

# Test OpenCV
import cv2
print(f"✅ OpenCV {cv2.__version__}")
```

## ⚙️ Configuration GPU (Optionnel)

### Pour NVIDIA GPU (CUDA)

```bash
# Installer PyTorch avec CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Installer PaddlePaddle GPU
pip install paddlepaddle-gpu
```

Puis dans `config.py`:
```python
PADDLE_OCR_USE_GPU = True
YOLO_DEVICE = "cuda"
```

### Pour Mac (Apple Silicon)

```python
# Dans config.py
YOLO_DEVICE = "mps"  # Metal Performance Shaders
```

## 📂 Structure des Modèles

```
MUAG/
├── models/  (créé automatiquement)
│   ├── paddle_ocr/  (modèles PaddleOCR)
│   └── yolo/        (modèles YOLOv11)
└── data/
    └── screenshots/ (captures CUA)
```

## 🚀 Premier Lancement

Au premier lancement du CUA Agent:
1. PaddleOCR télécharge les modèles OCR (fr + en) - ~3 min
2. YOLOv11 télécharge le modèle - ~1 min
3. Le système vérifie OpenCV

Console attendue:
```
🔄 Initialisation PaddleOCR...
📥 Téléchargement modèles OCR...
✅ PaddleOCR chargé (fr, en)

🔄 Initialisation YOLOv11...
📥 Téléchargement yolov11m.pt...
✅ YOLOv11 chargé

✅ Tous les modules vision OK!
```

## 🐛 Dépannage

### Erreur "No module named 'paddle'"
```bash
pip install paddlepaddle --upgrade
```

### Erreur "ultralytics not found"
```bash
pip install ultralytics --upgrade
```

### Performance lente
- Réduire résolution screenshots dans config
- Utiliser yolov11n.pt au lieu de yolov11m.pt
- Désactiver preprocessing avancé

### Out of Memory
- Mettre YOLO_DEVICE = "cpu"
- Réduire MONITOR_HISTORY_SIZE dans config

## 📊 Performances Attendues

**CPU (8 cores, 16GB RAM):**
- PaddleOCR: ~1-2s par frame
- YOLOv11m: ~0.5-1s par frame
- Total pipeline: ~3-4s par cycle

**GPU (NVIDIA RTX):**
- PaddleOCR: ~0.3-0.5s
- YOLOv11m: ~0.1-0.2s
- Total pipeline: ~1s par cycle

## ✅ Vérification Finale

Lancez:
```bash
python test_vision_setup.py
```

Doit afficher:
```
✅ PaddleOCR: OK
✅ YOLOv11: OK  
✅ OpenCV: OK
✅ Vision Pipeline Ready!
```
