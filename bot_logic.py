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
    def _click_line(self, region, keywords):
        pos = find_text_position(region, keywords)
        if pos:
            x, y, line_text = pos
            pyautogui.click(x, y)
            self.log(f"Клик по строке: \"{line_text.strip()}\"")
            return True
        return False

    def _check_target(self):
        region = self.regions["fish_label"]
        text = ocr_text(grab(region)).lower()
        return (self.target in text), text

    # ------------------------------------------------------------------
    def _run(self):
        self.log("Бот запущен.")
        last_action_time = 0.0

        while not self._stop_event.is_set():
            if self.max_attempts and self.attempts >= self.max_attempts:
                self.log(f"Достигнут лимит попыток ({self.max_attempts}). Остановка.")
                break

            found, label_text = self._check_target()
            if found:
                self.found = True
                self.log(f"Найдена нужная мутация/размер! Текст: \"{label_text.strip()}\"")
                self.log("Останавливаю бота.")
                break

            now = time.time()
            if now - last_action_time < self.click_delay:
                time.sleep(self.poll_interval)
                continue

            dialog_region = self.regions["dialog"]

            # 1. Подтверждение оплаты ("Ready?" -> "Yes!")
            if self._click_line(dialog_region, self.appraiser_cfg["confirm_keywords"]):
                last_action_time = time.time()
                time.sleep(self.click_delay)
                continue

            # 2. Запрос оценки / повторной оценки
            if self._click_line(dialog_region, self.appraiser_cfg["ask_keywords"]):
                last_action_time = time.time()
                self.attempts += 1
                self.log(f"Попытка оценки №{self.attempts}")
                time.sleep(self.click_delay)
                continue

            # Ничего подходящего не найдено — ждём следующего опроса
            time.sleep(self.poll_interval)

        self.log("Цикл завершён.")
