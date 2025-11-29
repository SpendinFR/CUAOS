import cv2
from pathlib import Path
from actions.vision_preprocessing import preprocessor
from actions.paddle_ocr_detector import paddle_ocr

# Test avec screenshot existant
screenshot = Path("data/screenshots/cua_step_2.png")

if screenshot.exists():
    print(f"Test avec: {screenshot}")
    
    # Charger image
    image = cv2.imread(str(screenshot))
    print(f"Image originale: {image.shape}")
    
    # PREPROCESSING (downscale auto)
    image = preprocessor.preprocess(image)
    
    print("Detection OCR...")
    result = paddle_ocr.detect_text(image)
    
    print(f"\nNombre de textes detectes: {len(result)}")
    
    if result:
        print("\nPREMIERS TEXTES:")
        for i, det in enumerate(result[:15]):
            text = det['text']
            conf = det['confidence']
            print(f"  {i+1}. '{text}' (confiance: {conf:.2f})")
    else:
        print("AUCUN TEXTE DETECTE!")
else:
    print(f"Screenshot non trouve: {screenshot}")
