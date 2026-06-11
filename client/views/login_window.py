# ============================================================
# Окно авторизации
# ============================================================

import customtkinter as ctk
from api_client import ApiClient


class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.client = ApiClient()
        self._login_in_progress = False

        self.title("АИС Библиотека")
        self.geometry("500x580")
        self.resizable(False, False)
        self.configure(fg_color="#f0f2f5")

        # Центрируем окно
        self.update_idletasks()
        from utils import center_dialog
        center_dialog(self, 500, 580, resizable=False)

        # Карточка входа
        card = ctk.CTkFrame(self, corner_radius=16, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(expand=True, fill="both", padx=25, pady=25)

        # Заголовок
        ctk.CTkLabel(card, text="Библиотека",
                     font=("Segoe UI", 28, "bold"), text_color="#1a1a2e").pack(pady=(35, 5))
        ctk.CTkLabel(card, text="Автоматизированная информационная система",
                     font=("Segoe UI", 13), text_color="#6e7781").pack(pady=(0, 25))

        ctk.CTkLabel(card, text="Вход в систему",
                     font=("Segoe UI", 17, "bold"), text_color="#24292f").pack(pady=(0, 15))

        # Поля
        lbl_row_login = ctk.CTkFrame(card, fg_color="transparent")
        lbl_row_login.pack(fill="x", pady=(6, 0), padx=10)
        ctk.CTkLabel(lbl_row_login, text="Логин", font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
        self.hint_login = ctk.CTkLabel(lbl_row_login, text="", font=("Segoe UI", 11), text_color="#c62828")
        self.hint_login.pack(side="left", padx=(6, 0))
        self.entry_login = ctk.CTkEntry(card, placeholder_text="Введите логин", width=340, height=44,
                                        font=("Segoe UI", 14),
                                        border_color="#d0d7de", fg_color="#f6f8fa")
        self.entry_login.pack(fill="x", pady=(0, 4), padx=10)

        lbl_row_pass = ctk.CTkFrame(card, fg_color="transparent")
        lbl_row_pass.pack(fill="x", pady=(6, 0), padx=10)
        ctk.CTkLabel(lbl_row_pass, text="Пароль", font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
        self.hint_password = ctk.CTkLabel(lbl_row_pass, text="", font=("Segoe UI", 11), text_color="#c62828")
        self.hint_password.pack(side="left", padx=(6, 0))
        self.entry_password = ctk.CTkEntry(card, placeholder_text="Введите пароль", show="●", width=340, height=44,
                                           font=("Segoe UI", 14),
                                           border_color="#d0d7de", fg_color="#f6f8fa")
        self.entry_password.pack(fill="x", pady=(0, 4), padx=10)

        from utils import add_live_validation_with_hint, validate_login, validate_password
        add_live_validation_with_hint(self.entry_login, validate_login, self.hint_login)
        add_live_validation_with_hint(self.entry_password, validate_password, self.hint_password)

        # Предупреждение о техобслуживании
        self.maintenance_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 15),
                                               text_color="#e65100")
        self.maintenance_label.pack(pady=(0, 5))

        # Кнопка
        ctk.CTkButton(card, text="Войти", width=340, height=46,
                      font=("Segoe UI", 15, "bold"),
                      fg_color="#2e7d32", hover_color="#1b5e20",
                      command=self._login).pack(pady=(15, 5))

        # Сообщение об ошибке
        self.error_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 14), text_color="#c62828",
                                         wraplength=440, justify="center", width=440)
        self.error_label.pack(pady=(0, 5), padx=5)

        # Enter = вход
        self.bind("<Return>", lambda e: self._login())
        self.entry_login.focus()

        self._check_maintenance()

    def _check_maintenance(self):
        def fetch():
            return self.client.get_maintenance()

        def on_ok(data):
            if data.get("maintenance"):
                self.maintenance_label.configure(
                    text="⚠ Ведутся технические работы.\nДоступ только для администраторов."
                )

        def on_err(_e):
            pass

        from utils import run_async
        run_async(self, fetch, on_ok, on_err)

    def _login(self):
        if self._login_in_progress:
            return
        login = self.entry_login.get().strip()
        password = self.entry_password.get().strip()
        self.error_label.configure(text="")
        from utils import validate_login, validate_password
        for err in [validate_login(login), validate_password(password)]:
            if err:
                self.error_label.configure(text=err)
                return
        self._login_in_progress = True

        def do_login():
            return self.client.login(login, password)

        def on_success(data):
            try:
                self.withdraw()
            except Exception:
                pass
            self.after(100, lambda: (self.destroy(), self.on_login_success(self.client)))

        def on_error(e):
            self._login_in_progress = False
            if e is None:
                msg = "Ошибка входа: сервер вернул неизвестную ошибку (возможно, аккаунт заблокирован)"
            else:
                msg = str(e)
                if msg == "None" or not msg:
                    msg = "Не удалось подключиться к серверу. Проверьте, запущен ли сервер."
            self.error_label.configure(text=msg)

        from utils import run_async
        run_async(self, do_login, on_success, on_error)
