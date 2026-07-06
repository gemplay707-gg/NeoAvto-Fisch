"""
vision.py
Захват участков экрана и распознавание текста (OCR) через Tesseract.

ВАЖНО: для работы нужен установленный движок Tesseract-OCR (не только
python-пакет pytesseract, а сам исполняемый файл). См. README.md.

Если Tesseract не находится в PATH, раскомментируйте и укажите путь ниже:
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
"""

import mss
import numpy as np
import cv2
import pytesseract
from PIL import Image

# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def grab(region: dict) -> Image.Image:
    """
    Делает скриншот указанного региона экрана.
    region: {"left": int, "top": int, "width": int, "height": int}
    Возвращает PIL.Image в RGB.
    """
    with mss.mss() as sct:
        shot = sct.grab(region)
        img = np.array(shot)  # BGRA
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        return Image.fromarray(img)


def _preprocess(img: Image.Image, scale: int = 2) -> Image.Image:
    """Увеличивает и бинаризует изображение — заметно повышает точность OCR
    на игровом UI с полупрозрачным текстом."""
    gray = img.convert("L")
    w, h = gray.size
    gray = gray.resize((w * scale, h * scale), Image.LANCZOS)
    arr = np.array(gray)
    _, thresh = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)


def ocr_text(img: Image.Image, preprocess: bool = True) -> str:
    """Возвращает весь распознанный текст региона в виде строки."""
    proc = _preprocess(img) if preprocess else img
    return pytesseract.image_to_string(proc, lang="eng")


def ocr_data(img: Image.Image, preprocess: bool = True, scale: int = 2):
    """
    Возвращает "сырые" данные OCR (слова + их координаты) вместе
    с использованным коэффициентом масштабирования (нужен для пересчёта
    координат обратно в координаты исходного скриншота).
    """
    if preprocess:
        proc = _preprocess(img, scale=scale)
        used_scale = scale
    else:
        proc = img
        used_scale = 1
    data = pytesseract.image_to_data(proc, lang="eng", output_type=pytesseract.Output.DICT)
    return data, used_scale


def find_text_position(region: dict, keywords):
    """
    Ищет в указанном регионе экрана строку, содержащую любое из ключевых слов
    (без учёта регистра). Строки группируются по (block, par, line) — так,
    как их видит Tesseract.

    Возвращает (abs_x, abs_y, line_text) — абсолютные координаты центра
    найденной строки на экране (для клика) — или None, если не найдено.
    """
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