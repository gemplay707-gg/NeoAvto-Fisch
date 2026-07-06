"""
calibration.py
Полноэкранное окно для выделения прямоугольной области мышью
(зажать ЛКМ, потянуть, отпустить). Esc — отмена.
"""

import tkinter as tk


class RegionSelector:
    def __init__(self, parent, title="Выделите область"):
        self.result = None
        self.parent = parent

        # Используем Toplevel вместо tk.Tk(), привязывая его к главному окну
        self.root = tk.Toplevel(parent)
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.30)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        self.root.title(title)

        self.canvas = tk.Canvas(self.root, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.root.bind("<Escape>", lambda e: self._cancel())

        tk.Label(
            self.root, text=f"{title}   (Esc — отмена)",
            fg="white", bg="black", font=("Arial", 16)
        ).place(x=20, y=20)

    def _on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="#ff3333", width=2
        )

    def _on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def _on_release(self, event):
        x0, y0 = self.start_x, self.start_y
        x1, y1 = event.x, event.y
        left, top = min(x0, x1), min(y0, y1)
        width, height = abs(x1 - x0), abs(y1 - y0)
        if width > 5 and height > 5:
            self.result = {"left": int(left), "top": int(top),
                            "width": int(width), "height": int(height)}
        self.root.destroy()

    def _cancel(self):
        self.result = None
        self.root.destroy()

    def run(self):
        # Делаем окно калибровки активным и перехватываем фокус
        self.root.focus_set()
        self.root.grab_set()
        # Корректно ждем, пока пользователь выделит область или нажмет Esc
        self.parent.wait_window(self.root)
        return self.result


def select_region(parent, title="Выделите область"):
    return RegionSelector(parent, title).run()