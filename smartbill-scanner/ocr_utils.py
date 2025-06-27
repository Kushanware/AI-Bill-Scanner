from PIL import Image
import pytesseract
import cv2
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_file):
    image = Image.open(image_file).convert('L')  # Grayscale
    img_np = np.array(image)
    # Thresholding
    _, img_bin = cv2.threshold(img_np, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # Denoising
    img_denoised = cv2.fastNlMeansDenoising(img_bin, h=30)
    return Image.fromarray(img_denoised)

def extract_text_from_image(image_path_or_file):
    preprocessed = preprocess_image(image_path_or_file)
    text = pytesseract.image_to_string(preprocessed)
    return text 