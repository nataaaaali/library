# ============================================================
# Вкладка "Администрирование"
# ============================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from utils import translate_role, translate_action, format_datetime, run_async


class AdminTab:
    def __init__(self, parent, client):
        self.client = client
        self.parent = parent

        self.tabview = ctk.CTkTabview(parent, corner_radius=10,
                                      fg_color="white",
                                      border_width=1, border_color="#d0d7de")
        self.tabview.pack(fill="both", expand=True, padx=5, pady=5)

        tab_users = self.tabview.add("Пользователи")
        tab_logs = self.tabview.add("Логи")

        self._build_users_tab(tab_users)
        self._build_logs_tab(tab_logs)

    def _show_status(self, text, color="gray"):
        if hasattr(self, "status_label"):
            self.status_label.configure(text=text, text_color=color)
            self.parent.after(5000, lambda: self.status_label.configure(text=""))

    def _sort_column(self, tree, col):
        from utils import sort_treeview
        reverse = getattr(self, "_sort_reverse", {}).get(col, False)
        sort_treeview(tree, col, reverse)
        self._sort_reverse = getattr(self, "_sort_reverse", {})
        self._sort_reverse[col] = not reverse

    def _format_fio(self, u: dict) -> str:
        parts = [
            u.get("last_name", ""),
            u.get("first_name", ""),
            (u.get("middle_name") or "")
        ]
        return " ".join(p for p in parts if p).strip()

    def _build_users_tab(self, parent):
        header = ctk.CTkLabel(parent, text="Управление пользователями",
                              font=("Segoe UI", 18, "bold"), text_color="#24292f")
        header.pack(pady=(10, 5))

        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("id", "login", "full_name", "role")
        self.tree_users = ttk.Treeview(card, columns=cols, show="headings", height=12)
        self.tree_users.heading("id", text="ID", command=lambda: self._sort_column(self.tree_users, "id"))
        self.tree_users.heading("login", text="Логин", command=lambda: self._sort_column(self.tree_users, "login"))
        self.tree_users.heading("full_name", text="ФИО", command=lambda: self._sort_column(self.tree_users, "full_name"))
        self.tree_users.heading("role", text="Роль", command=lambda: self._sort_column(self.tree_users, "role"))

        self.tree_users.column("id", anchor="center")
        self.tree_users.column("login")
        self.tree_users.column("full_name")
        self.tree_users.column("role", anchor="center")
        from utils import bind_tree_columns
        bind_tree_columns(self.tree_users, {
            "id": 0.08, "login": 0.22, "full_name": 0.45, "role": 0.25
        })

        scroll = ctk.CTkScrollbar(card, command=self.tree_users.yview)
        self.tree_users.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree_users.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.tree_users.tag_configure("admin", foreground="#1565c0")
        self.tree_users.tag_configure("librarian", foreground="#2e7d32")
        self.tree_users.tag_configure("even", background="#f6f8fa")

        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Добавить библиотекаря", command=self._add_librarian,
                      width=180, height=38, font=("Segoe UI", 14, "bold"),
                      fg_color="#2e7d32", hover_color="#1b5e20").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Удалить", command=self._delete_user,
                      width=120, height=38, font=("Segoe UI", 14, "bold"),
                      fg_color="#c62828", hover_color="#b71c1c").pack(side="left", padx=5)
        self._maintenance_var = tk.IntVar(value=0)
        self.switch_maintenance = ctk.CTkSwitch(
            btn_frame, text="Тех. обслуживание",
            variable=self._maintenance_var,
            command=self._on_maintenance_switch,
            font=("Segoe UI", 14),
            progress_color="#e65100",
            button_color="#ffffff",
            button_hover_color="#f0f0f0"
        )
        self.switch_maintenance.pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(parent, text="", font=("Segoe UI", 14))
        self.status_label.pack(fill="x", padx=10, pady=(0, 5))

        self._load_users()
        self._fetch_maintenance_state()

    def _load_users(self):
        def fetch():
            return self.client.get("/users")

        def on_success(users):
            for item in self.tree_users.get_children():
                self.tree_users.delete(item)
            for i, u in enumerate(users):
                fio = self._format_fio(u)
                role = translate_role(u.get("role", ""))
                tag = u.get("role", "")
                if i % 2 == 0:
                    tag = (tag, "even") if tag else "even"
                self.tree_users.insert("", "end", values=(
                    u.get("id"), u.get("login"), fio, role
                ), tags=tag if isinstance(tag, str) else tag)

        def on_error(e):
            self._show_status(f"Ошибка загрузки: {e}", "#c62828")

        run_async(self.parent, fetch, on_success, on_error)

    def _add_librarian(self):
        dlg = ctk.CTkToplevel(self.parent)
        dlg.title("Новый библиотекарь")
        dlg.grab_set()
        dlg.configure(fg_color="#f0f2f5")
        dlg.transient(self.parent)
        dlg.withdraw()
        from utils import center_dialog
        def _place():
            center_dialog(dlg, 440, None, resizable=True)
            dlg.deiconify()
        dlg.after(100, _place)

        card = ctk.CTkFrame(dlg, corner_radius=12, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(card, text="Добавление библиотекаря",
                     font=("Segoe UI", 20, "bold"), text_color="#24292f").pack(pady=(15, 12))

        frame = ctk.CTkFrame(card, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=5)

        fields = [
            ("Логин *", "login"),
            ("Пароль *", "password"),
            ("Фамилия *", "last_name"),
            ("Имя *", "first_name"),
            ("Отчество", "middle_name"),
        ]
        self.entries = {}
        self.hints = {}
        from utils import add_live_validation_with_hint, validate_login, validate_password, validate_name
        for label_text, key in fields:
            lbl_row = ctk.CTkFrame(frame, fg_color="transparent")
            lbl_row.pack(fill="x", pady=(2, 0))
            ctk.CTkLabel(lbl_row, text=label_text, font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
            hint = ctk.CTkLabel(lbl_row, text="", font=("Segoe UI", 11), text_color="#c62828")
            hint.pack(side="left", padx=(6, 0))
            show = "*" if key == "password" else ""
            ent = ctk.CTkEntry(frame, width=360, height=38, font=("Segoe UI", 14),
                               border_color="#d0d7de", fg_color="#f6f8fa", show=show)
            ent.pack(fill="x", pady=(0, 4))
            if key == "login":
                add_live_validation_with_hint(ent, validate_login, hint)
            elif key == "password":
                add_live_validation_with_hint(ent, validate_password, hint)
            elif key in ("last_name", "first_name"):
                add_live_validation_with_hint(ent, lambda v, lt=label_text: validate_name(v, lt.replace(" *", "")), hint)
            elif key == "middle_name":
                add_live_validation_with_hint(ent, lambda v: validate_name(v, "Отчество", required=False), hint)
            self.entries[key] = ent
            self.hints[key] = hint

        error_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 14), text_color="#c62828")
        error_label.pack(pady=(5, 0))

        def save():
            login = self.entries["login"].get().strip()
            password = self.entries["password"].get().strip()
            ln = self.entries["last_name"].get().strip()
            fn = self.entries["first_name"].get().strip()
            mn = self.entries["middle_name"].get().strip() or None
            from utils import validate_login, validate_password, validate_name
            for err in [validate_login(login), validate_password(password),
                        validate_name(ln, "Фамилия"), validate_name(fn, "Имя"),
                        validate_name(mn or "", "Отчество", required=False)]:
                if err:
                    error_label.configure(text=err)
                    return
            data = {
                "login": login, "password": password,
                "last_name": ln, "first_name": fn,
                "middle_name": self.entries["middle_name"].get().strip() or None,
            }

            def do_post():
                return self.client.post("/users", data)

            def on_ok(_):
                dlg.after(50, dlg.destroy)
                self._show_status("Библиотекарь добавлен", "#2e7d32")
                self._load_users()

            def on_err(e):
                error_label.configure(text=str(e))

            run_async(dlg, do_post, on_ok, on_err)

        ctk.CTkButton(card, text="Добавить", command=save,
                      width=200, height=42, font=("Segoe UI", 15, "bold"),
                      fg_color="#2e7d32", hover_color="#1b5e20").pack(pady=8)

    def _delete_user(self):
        sel = self.tree_users.selection()
        if not sel:
            self._show_status("Выберите пользователя", "#c62828")
            return
        values = self.tree_users.item(sel[0], "values")
        user_id = values[0]
        role = values[3]
        fio = values[2]
        if role == "Администратор":
            self._show_status("Нельзя удалить администратора", "#c62828")
            return

        from tkinter import messagebox
        if not messagebox.askyesno("Подтверждение", f"Удалить пользователя\n{fio}\n(логин: {values[1]})?"):
            return

        def do_del():
            return self.client.delete(f"/users/{user_id}")

        def on_ok(_):
            self._show_status("Пользователь удален", "#2e7d32")
            self._load_users()

        def on_err(e):
            self._show_status(f"Ошибка: {e}", "#c62828")

        run_async(self.parent, do_del, on_ok, on_err)

    def _fetch_maintenance_state(self):
        def do_get():
            return self.client.get_maintenance()

        def on_ok(data):
            self._maintenance_var.set(1 if data.get("maintenance") else 0)

        def on_err(_e):
            pass

        run_async(self.parent, do_get, on_ok, on_err)

    def _on_maintenance_switch(self):
        def do_post():
            return self.client.post("/maintenance/toggle", {})

        def on_ok(data):
            self._maintenance_var.set(1 if data.get("maintenance") else 0)
            status = "включён" if data.get("maintenance") else "выключён"
            self._show_status(f"Режим тех. обслуживания {status}", "#e65100")

        def on_err(e):
            self._maintenance_var.set(1 - self._maintenance_var.get())
            self._show_status(f"Ошибка: {e}", "#c62828")

        run_async(self.parent, do_post, on_ok, on_err)

    def _build_logs_tab(self, parent):
        header = ctk.CTkLabel(parent, text="Журнал действий",
                              font=("Segoe UI", 18, "bold"), text_color="#24292f")
        header.pack(pady=(10, 5))

        # Фильтры
        filter_frame = ctk.CTkFrame(parent, corner_radius=10, fg_color="white",
                                    border_width=1, border_color="#d0d7de")
        filter_frame.pack(fill="x", padx=10, pady=5)

        from utils import ACTION_CHOICES
        ctk.CTkLabel(filter_frame, text="Действие:", font=("Segoe UI", 14), text_color="#24292f").pack(side="left", padx=(12, 4), pady=10)
        self.log_filter_action = ctk.CTkComboBox(filter_frame, values=[v for _, v in ACTION_CHOICES], width=180, height=32, font=("Segoe UI", 14))
        self.log_filter_action.pack(side="left", padx=4, pady=10)
        self.log_filter_action.set("Все")

        ctk.CTkLabel(filter_frame, text="Пользователь:", font=("Segoe UI", 14), text_color="#24292f").pack(side="left", padx=(8, 4), pady=10)
        self.log_filter_user = ctk.CTkEntry(filter_frame, width=140, height=32, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        self.log_filter_user.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(filter_frame, text="С:", font=("Segoe UI", 14), text_color="#24292f").pack(side="left", padx=(8, 4), pady=10)
        from tkcalendar import DateEntry
        from datetime import date
        try:
            self.log_filter_from = DateEntry(filter_frame, date_pattern="dd.mm.yyyy", width=12, background="#2e7d32", foreground="white", borderwidth=0, locale="ru_RU")
        except Exception:
            self.log_filter_from = DateEntry(filter_frame, date_pattern="dd.mm.yyyy", width=12, background="#2e7d32", foreground="white", borderwidth=0)
        self.log_filter_from.set_date(date(2000, 1, 1))
        self.log_filter_from.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(filter_frame, text="По:", font=("Segoe UI", 14), text_color="#24292f").pack(side="left", padx=(8, 4), pady=10)
        try:
            self.log_filter_to = DateEntry(filter_frame, date_pattern="dd.mm.yyyy", width=12, background="#2e7d32", foreground="white", borderwidth=0, locale="ru_RU")
        except Exception:
            self.log_filter_to = DateEntry(filter_frame, date_pattern="dd.mm.yyyy", width=12, background="#2e7d32", foreground="white", borderwidth=0)
        self.log_filter_to.set_date(date.today())
        self.log_filter_to.pack(side="left", padx=4, pady=10)

        ctk.CTkButton(filter_frame, text="Применить", width=90, height=32, font=("Segoe UI", 15, "bold"), command=self._load_logs).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(filter_frame, text="Сбросить", width=90, height=32, font=("Segoe UI", 15, "bold"),
                      fg_color="#6a737d", hover_color="#484f58",
                      command=self._reset_logs_filters).pack(side="left", padx=4, pady=10)

        # Таблица
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("id", "time", "login", "action", "details")
        self.tree_logs = ttk.Treeview(card, columns=cols, show="headings", height=12)
        self.tree_logs.heading("id", text="ID")
        self.tree_logs.heading("time", text="Время", command=lambda: self._sort_column(self.tree_logs, "time"))
        self.tree_logs.heading("login", text="Пользователь", command=lambda: self._sort_column(self.tree_logs, "login"))
        self.tree_logs.heading("action", text="Действие", command=lambda: self._sort_column(self.tree_logs, "action"))
        self.tree_logs.heading("details", text="Детали", command=lambda: self._sort_column(self.tree_logs, "details"))

        self.tree_logs.column("id", width=0, stretch=False)
        self.tree_logs.column("time", anchor="center")
        self.tree_logs.column("login")
        self.tree_logs.column("action")
        self.tree_logs.column("details")
        from utils import bind_tree_columns
        bind_tree_columns(self.tree_logs, {
            "id": 0, "time": 0.15, "login": 0.20, "action": 0.20, "details": 0.45
        })

        scroll = ctk.CTkScrollbar(card, command=self.tree_logs.yview)
        self.tree_logs.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree_logs.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.tree_logs.tag_configure("even", background="#f6f8fa")

        # Пагинация
        pag_frame = ctk.CTkFrame(parent, fg_color="transparent")
        pag_frame.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkButton(pag_frame, text="Обновить", command=self._load_logs,
                      width=100, height=34, font=("Segoe UI", 14, "bold"),
                      fg_color="#1565c0", hover_color="#0d47a1").pack(side="left", padx=5)
        ctk.CTkButton(pag_frame, text="← Назад", command=self._logs_prev,
                      width=100, height=34, font=("Segoe UI", 14, "bold")).pack(side="left", padx=5)
        self.logs_page_label = ctk.CTkLabel(pag_frame, text="", font=("Segoe UI", 14), text_color="#24292f")
        self.logs_page_label.pack(side="left", padx=10)
        ctk.CTkButton(pag_frame, text="Вперёд →", command=self._logs_next,
                      width=100, height=34, font=("Segoe UI", 14, "bold")).pack(side="left", padx=5)

        self.logs_offset = 0
        self.logs_limit = 50
        self.logs_total = 0
        self._load_logs()
        # Автообновление каждые 30 секунд
        self._schedule_logs_refresh()

    def _schedule_logs_refresh(self):
        self._logs_refresh_job = self.parent.after(30000, self._auto_refresh_logs)

    def _auto_refresh_logs(self):
        self._load_logs()
        self._schedule_logs_refresh()

    def _reset_logs_filters(self):
        from datetime import date
        self.log_filter_action.set("Все")
        self.log_filter_user.delete(0, "end")
        self.log_filter_from.set_date(date(2000, 1, 1))
        self.log_filter_to.set_date(date.today())
        self.logs_offset = 0
        self._load_logs()

    def _logs_prev(self):
        if self.logs_offset >= self.logs_limit:
            self.logs_offset -= self.logs_limit
            self._load_logs()

    def _logs_next(self):
        if self.logs_offset + self.logs_limit < self.logs_total:
            self.logs_offset += self.logs_limit
            self._load_logs()

    def _load_logs(self):
        def fetch():
            from utils import ACTION_CHOICES
            action_map = {v: k for k, v in ACTION_CHOICES}
            action_val = action_map.get(self.log_filter_action.get(), "")
            params = {
                "limit": self.logs_limit,
                "offset": self.logs_offset,
            }
            if action_val:
                params["action"] = action_val
            user_q = self.log_filter_user.get().strip()
            if user_q:
                params["user_query"] = user_q
            date_from = self.log_filter_from.get().strip()
            if date_from:
                params["date_from"] = date_from
            date_to = self.log_filter_to.get().strip()
            if date_to:
                params["date_to"] = date_to
            return self.client.get("/logs", params=params)

        def on_success(data):
            logs = data.get("logs", [])
            self.logs_total = data.get("total", 0)
            for item in self.tree_logs.get_children():
                self.tree_logs.delete(item)
            for i, log in enumerate(logs):
                tag = "even" if i % 2 == 0 else ""
                self.tree_logs.insert("", "end", values=(
                    log.get("id"),
                    format_datetime(log.get("created_at", "")),
                    log.get("user_display", "Система"),
                    translate_action(log.get("action", "")),
                    log.get("details", ""),
                ), tags=(tag,))
            start = self.logs_offset + 1 if logs else 0
            end = self.logs_offset + len(logs)
            self.logs_page_label.configure(text=f"{start}–{end} из {self.logs_total}")

        def on_error(e):
            if hasattr(self, "status_label"):
                self._show_status(f"Ошибка загрузки логов: {e}", "#c62828")

        run_async(self.parent, fetch, on_success, on_error)
