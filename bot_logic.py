"""
bot_logic.py
Основной цикл бота: следит за диалогом NPC-оценщика, кликает нужные
строки, проверяет текст с названием рыбы на наличие целевой мутации/размера.
"""

import time
import threading

import pyautogui

import config
from vision import grab, ocr_text, find_text_position

pyautogui.FAILSAFE = True  # увести мышь в угол экрана = аварийный стоп pyautogui


class FischAppraiserBot:
    def __init__(self, regions, appraiser, target, log_callback=None,
                 max_attempts=0, click_delay=0.9, poll_interval=0.4):
        """
        regions: dict с регионами "fish_label" и "dialog"
        appraiser: имя оценщика (ключ в config.APPRAISERS)
        target: искомая мутация/размер (строка из config.ALL_TARGETS)
        max_attempts: 0 = без лимита, иначе останавливается после N попыток оценки
        """
        self.regions = regions
        self.appraiser_cfg = config.APPRAISERS[appraiser]
        self.target = target.lower()
        self.log = log_callback or (lambda msg: None)
        self.max_attempts = max_attempts
        self.click_delay = click_delay
        self.poll_interval = poll_interval

        self._stop_event = threading.Event()
        self._thread = None
        self.attempts = 0
        self.found = False

    # ------------------------------------------------------------------
    def start(self):
        self._stop_event.clear()
        self.attempts = 0
        self.found = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------
    def _run(self):
        self.log("Бот запущен.")
        last_action_time = 0.0

        # Защитная проверка на случай пустой цели
        if not self.target:
            self.log("Ошибка: Не выбрана цель для поиска! Остановка.")
            return

        while not self._stop_event.is_set():
            if self.max_attempts and self.attempts >= self.max_attempts:
                self.log(f"Достигнут лимит попыток ({self.max_attempts}). Остановка.")
                break

            # 1. Проверяем область названия рыбы
            found, label_text = self._check_target()
            
            # ВЫВОДИМ В ЛОГ ВСЁ, ЧТО ВИДИТ ТЕССЕРАКТ В ОБЛАСТИ РЫБЫ
            clean_text = label_text.replace('\n', ' ').strip()
            self.log(f"[Отладка OCR] Текст рыбы: '{clean_text}' (Ищем: '{self.target}')")

            if found:
                self.found = True
                self.log(f"Найдена нужная мутация/размер! Текст: \"{clean_text}\"")
                self.log("Останавливаю бота.")
                break

            now = time.time()
            if now - last_action_time < self.click_delay:
                time.sleep(self.poll_interval)
                continue

            dialog_region = self.regions["dialog"]

            # 2. Подтверждение оплаты ("Ready?" -> "Yes!")
            if self._click_line(dialog_region, self.appraiser_cfg["confirm_keywords"]):
                self.log(" -> Найдена кнопка подтверждения оплаты (Yes/Ready). Кликаю.")
                last_action_time = time.time()
                time.sleep(self.click_delay)
                continue

            # 3. Запрос оценки / повторной оценки
            if self._click_line(dialog_region, self.appraiser_cfg["ask_keywords"]):
                last_action_time = time.time()
                self.attempts += 1
                self.log(f"Попытка оценки №{self.attempts}")
                time.sleep(self.click_delay)
                continue

            # Если ничего не найдено, пишем легкую отладку, чтобы видеть, что бот не завис
            # Чтобы не спамить лог слишком сильно, можно ориентироваться на интервал опроса
            time.sleep(self.poll_interval)

        self.log("Цикл бота завершён.")

    # ------------------------------------------------------------------
    def _check_target(self):
        """Проверяет регион названия рыбы на наличие целевой мутации/размера."""
        if "fish_label" not in self.regions:
            return False, ""
        region = self.regions["fish_label"]
        try:
            text = ocr_text(grab(region)).lower()
            if self.target in text:
                return True, text
            return False, text
        except Exception as e:
            return False, f"Ошибка OCR: {str(e)}"

    def _click_line(self, region, keywords):
        """Ищет ключевые слова в регионе диалога и кликает, если находит."""
        try:
            pos = find_text_position(region, keywords)
            if pos:
                abs_x, abs_y, line_text = pos
                # Запоминаем текущую позицию мыши, чтобы не дергать экран игрока слишком сильно
                old_x, old_y = pyautogui.position()
                pyautogui.click(abs_x, abs_y)
                pyautogui.moveTo(old_x, old_y)  # возвращаем мышь назад
                return True
        except Exception as e:
            self.log(f"[Ошибка клика]: {str(e)}")
        return False