import cv2
from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='fr', use_angle_cls=True)

image = cv2.imread("data/screenshots/cua_step_2.png")
small = cv2.resize(image, (1280, 720))

result = ocr.ocr(small)

print(f"result = {result}")
print(f"type(result) = {type(result)}")
print(f"len(result) = {len(result)}")
print(f"type(result[0]) = {type(result[0])}")

# Test si c'est un dict
if isinstance(result[0], dict):
    print("C'EST UN DICT!")
    print(f"Keys: {list(result[0].keys())[:5]}")
    print(f"Values[0]: {list(result[0].values())[0]}")
else:
    print("C'EST UNE LISTE!")
    print(f"result[0][0] = {result[0][0]}")
