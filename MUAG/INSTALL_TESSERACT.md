# Guide d'installation Tesseract OCR pour Windows

## Installation Tesseract OCR

### Étape 1 : Télécharger Tesseract
- Téléchargez depuis : https://github.com/UB-Mannheim/tesseract/wiki
- Version recommandée : tesseract-ocr-w64-setup-5.3.3.20231005.exe (ou plus récent)

### Étape 2 : Installer
- Exécutez l'installateur
- **IMPORTANT** : Notez le chemin d'installation (par défaut : `C:\Program Files\Tesseract-OCR`)
- Cochez "Additional language data" et sélectionnez au moins :
  - English (eng)
  - French (fra)

### Étape 3 : Configurer le PATH (optionnel mais recommandé)
```powershell
# Ajouter au PATH système
setx PATH "%PATH%;C:\Program Files\Tesseract-OCR"
```

### Étape 4 : Vérifier l'installation
```powershell
tesseract --version
```

Devrait afficher quelque chose comme :
```
tesseract 5.3.3
```

### Étape 5 : Configurer pytesseract dans le code

Si Tesseract n'est PAS dans le PATH, ajoutez ceci à `config.py`:
```python
# Tesseract OCR Configuration
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

Et dans `cua_agent.py`, avant d'utiliser pytesseract:
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## Test Rapide

```python
import pytesseract
from PIL import Image

# Test
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
print(pytesseract.get_languages())
# Devrait afficher: ['eng', 'fra', 'osd']
```

## Langues Installées

Pour vérifier les langues :
```bash
tesseract --list-langs
```

Si besoin d'ajouter d'autres langues :
1. Téléchargez les fichiers `.traineddata` depuis https://github.com/tesseract-ocr/tessdata
2. Copiez-les dans `C:\Program Files\Tesseract-OCR\tessdata\`

## Dépannage

### Erreur "tesseract is not installed"
→ Vérifiez que Tesseract est installé et que le chemin est correct

### Erreur "Failed loading language"
→ Vérifiez que les fichiers de langue (eng.traineddata, fra.traineddata) sont dans tessdata/

### Performance lente
→ Normal ! OCR prend 1-3 secondes par capture d'écran
