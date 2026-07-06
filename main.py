"""
main.py
Графический интерфейс Fisch Appraiser Bot.
Поддержка горячих клавиш: F7 — старт, F8 — стоп.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import config
from calibration import select_region
from bot_logic import FischAppraiserBot

try:
    import keyboard  # глобальные горячие клавиши
    HAS_KEYBOARD = True
except Exception:
    HAS_KEYBOARD = False


class App:
    def __init__(self, root):
        self.root = root
        root.title("Fisch Appraiser Bot")
        root.geometry("580x560")
        root.minsize(520, 480)

        self.regions = config.load_regions()
        self.bot = None

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill="both", expand=True)

        # --- Оценщик ---
        ttk.Label(frm, text="Оценщик:").grid(row=0, column=0, sticky="w")
        self.appraiser_var = tk.StringVar(value="Drowned")
        appraiser_box = ttk.Combobox(
            frm, textvariable=self.appraiser_var,
            values=list(config.APPRAISERS.keys()), state="readonly"
        )
        appraiser_box.grid(row=0, column=1, sticky="ew", pady=4)

        # --- Цель ---
        ttk.Label(frm, text="Нужная мутация / размер:").grid(row=1, column=0, sticky="w")
        self.target_var = tk.StringVar()
        target_box = ttk.Combobox(
            frm, textvariable=self.target_var,
            values=config.ALL_TARGETS, state="readonly"
        )
        target_box.grid(row=1, column=1, sticky="ew", pady=4)
        if config.ALL_TARGETS:
            target_box.current(0)

        # --- Лимит попыток ---
        ttk.Label(frm, text="Лимит попыток (0 = без лимита):").grid(row=2, column=0, sticky="w")
        self.max_attempts_var = tk.StringVar(value="0")
        ttk.Entry(frm, textvariable=self.max_attempts_var).grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Separator(frm).grid(row=3, column=0, columnspan=2, sticky="ew", pady=8)

        # --- Калибровка ---
        ttk.Label(frm, text="Калибровка (сделайте один раз для вашего разрешения экрана):",
                  font=("Arial", 9, "italic")).grid(row=4, column=0, columnspan=2, sticky="w")
        ttk.Button(frm, text="Область названия рыбы / мутации",
                   command=self.calibrate_label).grid(row=5, column=0, columnspan=2, sticky="ew", pady=2)
        ttk.Button(frm, text="Область диалога NPC",
                   command=self.calibrate_dialog).grid(row=6, column=0, columnspan=2, sticky="ew", pady=2)

        ttk.Separator(frm).grid(row=7, column=0, columnspan=2, sticky="ew", pady=8)

        # --- Старт/Стоп ---
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=8, column=0, columnspan=2, sticky="ew")
        self.start_btn = ttk.Button(btn_frame, text="▶ Старт (F7)", command=self.start_bot)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=2)
        self.stop_btn = ttk.Button(btn_frame, text="■ Стоп (F8)", command=self.stop_bot, state="disabled")
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=2)

        hotkey_note = "F7 — Старт из игры | F8 — Аварийная остановка" if HAS_KEYBOARD else \
            "(модуль keyboard не найден — горячие клавиши недоступны)"
        ttk.Label(frm, text=hotkey_note, font=("Arial", 8, "bold"), foreground="green" if HAS_KEYBOARD else "red").grid(row=9, column=0, columnspan=2, sticky="w", pady=2)

        # --- Лог ---
        ttk.Label(frm, text="Лог:").grid(row=10, column=0, sticky="w", pady=(8, 0))
        self.log_box = tk.Text(frm, height=14, state="disabled", wrap="word")
        self.log_box.grid(row=11, column=0, columnspan=2, sticky="nsew", pady=4)

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(11, weight=1)

        if HAS_KEYBOARD:
            try:
                keyboard.add_hotkey("f7", self.start_bot)
                keyboard.add_hotkey("f8", self.stop_bot)
            except Exception:
                pass

        self.log(f"Регионы загружены: {self.regions}")

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def calibrate_label(self):
        self._calibrate("fish_label", "Выделите область с названием рыбы и мутацией")

    def calibrate_dialog(self):
        self._calibrate("dialog", "Выделите область с текстом диалога NPC")

    def _calibrate(self, key, title):
        self.root.withdraw()
        self.root.after(400, lambda: self._do_calibrate(key, title))

    def _do_calibrate(self, key, title):
        region = select_region(title)
        self.root.deiconify()
        if region:
            self.regions[key] = region
            config.save_regions(self.regions)
            self.log(f"Область '{key}' сохранена: {region}")
        else:
            self.log("Калибровка отменена.")

    def start_bot(self):
        if self.bot and self.bot.is_running():
            return

        target = self.target_var.get()
        if not target:
            messagebox.showwarning("Fisch Bot", "Выберите нужную мутацию/размер.")
            return

        try:
            max_attempts = int(self.max_attempts_var.get())
        except ValueError:
            max_attempts = 0

        self.bot = FischAppraiserBot(
            regions=self.regions,
            appraiser=self.appraiser_var.get(),
            target=target,
            log_callback=self.log,
            max_attempts=max_attempts,
        )
        self.bot.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.root.after(500, self._poll_bot)

    def stop_bot(self):
        if self.bot:
            self.bot.stop()

    def _poll_bot(self):
        if self.bot and self.bot.is_running():
            self.root.after(500, self._poll_bot)
        else:
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()