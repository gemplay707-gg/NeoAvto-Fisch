"""
config.py
Настройки, списки мутаций/размеров и хранение калибровки регионов экрана.
"""

import json
import os

# ---------------------------------------------------------------------------
# Пути
# ---------------------------------------------------------------------------
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".fisch_appraiser_bot")
os.makedirs(CONFIG_DIR, exist_ok=True)
REGIONS_FILE = os.path.join(CONFIG_DIR, "regions.json")

# ---------------------------------------------------------------------------
# Список мутаций (проценты не важны, важны только названия для сверки текста)
# ---------------------------------------------------------------------------
MUTATIONS = [
    "Albino", "Darkened", "Negative", "Glossy", "Jolly", "Lunar",
    "Translucent", "Electric", "Festive", "Hexed", "Silver", "Frozen",
    "Mosaic", "Scorched", "Amber", "Abyssal", "Coral", "Decayed", "Minty",
    "Poisoned", "Fossilized", "Vined", "Crimson", "Honey", "Midas",
    "New Years", "Beachy", "Boreal", "Eerie", "Fallen", "Frightful",
    "Lucky Gold", "Spooky", "Greedy", "Spirit", "Awesome", "Birthday",
    "Ghastly", "Gingerbread", "Gravy", "Jingle Bell", "Merry", "Mourned",
    "Mythical", "Peppermint", "Popsicle", "Shrouded", "Sinister", "Summer",
    "Sweet", "Liberty", "Beached", "Paradise", "Tanned", "Tropical",
    "Super-Tanned",
]

# Отдельная категория "размеров" (тоже отображается рядом с названием рыбы)
SIZES = ["Small", "Tiny", "Big", "Giant"]

# Единый список для выпадающего меню в GUI
ALL_TARGETS = MUTATIONS + SIZES

# ---------------------------------------------------------------------------
# Настройки оценщиков.
# Каждый оценщик описывается набором ключевых фраз, по которым бот понимает,
# какую строку диалога нужно нажать. Благодаря такой структуре в будущем
# легко добавить новых оценщиков — просто добавить новый ключ в словарь.
# ---------------------------------------------------------------------------
APPRAISERS = {
    "Drowned": {
        # Фразы начального/повторного запроса оценки -> всегда пункт "1."
        "ask_keywords": [
            "appraise this fish",
            "appraise it again",
        ],
        # Фразы подтверждения оплаты ("Ready?" -> "Yes!") -> тоже пункт "1."
        "confirm_keywords": [
            "ready?",
            "yes!",
        ],
    },
    # Пример на будущее:
    # "AnotherAppraiser": {
    #     "ask_keywords": [...],
    #     "confirm_keywords": [...],
    # },
}

# ---------------------------------------------------------------------------
# Регионы экрана по умолчанию (будут переопределены калибровкой пользователя)
# ---------------------------------------------------------------------------
DEFAULT_REGIONS = {
    "fish_label": {"top": 500, "left": 700, "width": 500, "height": 150},
    "dialog": {"top": 380, "left": 900, "width": 900, "height": 260},
}


def load_regions():
    """Загружает сохранённые регионы или возвращает регионы по умолчанию."""
    if os.path.exists(REGIONS_FILE):
        try:
            with open(REGIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = dict(DEFAULT_REGIONS)
                merged.update(data)
                return merged
        except Exception:
            pass
    return dict(DEFAULT_REGIONS)


def save_regions(regions):
    """Сохраняет регионы в json-файл конфигурации."""
    with open(REGIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(regions, f, ensure_ascii=False, indent=2)