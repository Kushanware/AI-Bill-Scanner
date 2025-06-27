from PIL import Image
import pytesseract
import cv2
import numpy as np
import requests
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_file):
    image = Image.open(image_file).convert('L')  # Grayscale
    img_np = np.array(image)
    # Thresholding
    _, img_bin = cv2.threshold(img_np, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # Denoising
    img_denoised = cv2.fastNlMeansDenoising(img_bin, h=30)
    return Image.fromarray(img_denoised)

def extract_text_from_image(image_file, api_key):
    url = 'https://api.ocr.space/parse/image'
    image_bytes = image_file.read()
    payload = {
        'isOverlayRequired': False,
        'apikey': api_key,
        'language': 'eng',
    }
    files = {
        'file': ('image.jpg', image_bytes),
    }
    response = requests.post(url, data=payload, files=files)
    result = response.json()
    try:
        return result['ParsedResults'][0]['ParsedText']
    except Exception:
        return "OCR failed or no text found."

def parse_bill_text(text):
    # Extract date (very basic, can be improved)
    date_match = re.search(r'(\d{2,4}[/-]\d{1,2}[/-]\d{1,4})', text)
    date = date_match.group(1) if date_match else "Not found"

    # Extract total (looks for 'total' followed by a number)
    total_match = re.search(r'total[^\d]*(\d+[\.,]?\d*)', text, re.IGNORECASE)
    if not total_match:
        # fallback: last number in the text
        numbers = re.findall(r'\d+[\.,]?\d*', text)
        total = numbers[-1] if numbers else "Not found"
    else:
        total = total_match.group(1)

    # Extract line items (very basic: lines with a number and a word)
    items = []
    for line in text.splitlines():
        if re.search(r'\d', line) and re.search(r'[a-zA-Z]', line):
            items.append(line.strip())
    return items, total, date 