"""
vision.py
Захват участков экрана и распознавание текста (OCR) через встроенный Tesseract.
Теперь бот портативный и не требует установки Tesseract в систему!
"""

import os
import sys
import mss
import numpy as np
import cv2
import pytesseract
from PIL import Image

# Автоматически определяем путь к папке приложения (работает и для .py, и для .exe)
if getattr(sys, 'frozen', False):
    # Если запущен скомпилированный .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Если запущен обычный .py файл
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Указываем путь к Tesseract прямо внутри папки нашего проекта
TESSERACT_PATH = os.path.join(BASE_DIR, "Tesseract-OCR", "tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def grab(region: dict) -> Image.Image:
    """Делает скриншот указанного региона экрана."""
    with mss.mss() as sct:
        shot = sct.grab(region)
        img = np.array(shot)  # BGRA
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        return Image.fromarray(img)


def _preprocess(img: Image.Image, scale: int = 2) -> Image.Image:
    """Увеличивает и бинаризует изображение — повышает точность OCR."""
    gray = img.convert("L")
    w, h = gray.size
    gray = gray.resize((w * scale, h * scale), Image.LANCZOS)
    arr = np.array(gray)
    _, thresh = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)


def ocr_text(img: Image.Image, preprocess: bool = True) -> str:
    """Возвращает весь распознанный текст региона в виде строки."""
    try:
        proc = _preprocess(img) if preprocess else img
        return pytesseract.image_to_string(proc, lang="eng")
    except Exception as e:
        return f"Ошибка OCR: {str(e)}\nПроверьте наличие папки Tesseract-OCR рядом с ботом!"


def ocr_data(img: Image.Image, preprocess: bool = True, scale: int = 2):
    """Возвращает 'сырые' данные OCR (слова + их координаты)."""
    if preprocess:
        proc = _preprocess(img, scale=scale)
        used_scale = scale
    else:
        proc = img
        used_scale = 1
    data = pytesseract.image_to_data(proc, lang="eng", output_type=pytesseract.Output.DICT)
    return data, used_scale


def find_text_position(region: dict, keywords):
    """Ищет в указанном регионе экрана строку, содержащую ключевые слова."""
    img = grab(region)
    data, used_scale = ocr_data(img)
    n = len(data["text"])

    lines = {}
    for i in range(n):
        txt = data["text"][i].strip()
        if not txt:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(i)

    for idxs in lines.values():
        line_text = " ".join(data["text"][i] for i in idxs)
        line_lower = line_text.lower()
        for kw in keywords:
            if kw.lower() in line_lower:
                xs = [data["left"][i] for i in idxs] + \
                     [data["left"][i] + data["width"][i] for i in idxs]
                ys = [data["top"][i] for i in idxs] + \
                     [data["top"][i] + data["height"][i] for i in idxs]
                cx = (min(xs) + max(xs)) / 2
                cy = (min(ys) + max(ys)) / 2
                abs_x = region["left"] + cx / used_scale
                abs_y = region["top"] + cy / used_scale
                return int(abs_x), int(abs_y), line_text
    return None