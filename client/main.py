# ============================================================
# Точка входа клиента АИС "Библиотека"
# ============================================================

import sys
import os

# Добавляем папку client в путь (для импортов)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.login_window import LoginWindow
from views.main_window import MainWindow
import customtkinter as ctk


def on_login_success(client):
    """Открывает главное окно после успешного входа."""
    app = MainWindow(client)
    app.mainloop()


def main():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Делаем шрифт кнопок более заметным по умолчанию
    _btn_orig = ctk.CTkButton.__init__
    def _btn_init(self, *args, **kwargs):
        if "font" not in kwargs:
            kwargs["font"] = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        _btn_orig(self, *args, **kwargs)
    ctk.CTkButton.__init__ = _btn_init

    login = LoginWindow(on_login_success)
    login.mainloop()


if __name__ == "__main__":
    main()
