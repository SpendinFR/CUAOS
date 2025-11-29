import cv2
from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='fr', use_angle_cls=True)

image = cv2.imread("data/screenshots/cua_step_2.png")
small = cv2.resize(image, (1280, 720))

result = ocr.ocr(small)

# Le format a change - c'est maintenant dict
if isinstance(result[0], dict):
    print("Format DICT (nouvelle version)")
    print(f"Keys: {result[0].keys()}")
    
    # Chercher la cle qui contient les lignes OCR
    for key in result[0].keys():
        if 'ocr' in key.lower() or 'text' in key.lower():
            print(f"\nCle OCR trouvee: {key}")
            lines = result[0][key]
            print(f"Type: {type(lines)}")
            if isinstance(lines, list):
                print(f"Nombre de lignes: {len(lines)}")
                if len(lines) > 0:
                    print(f"Exemple ligne[0]: {lines[0]}")
else:
    print("Format LISTE (ancienne version)")
    lines = result[0]
    print(f"Nombre de lignes: {len(lines)}")
    if len(lines) > 0:
        print(f"Exemple ligne[0]: {lines[0]}")
