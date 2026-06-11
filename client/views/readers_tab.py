# ============================================================
# Вкладка "Читатели"
# ============================================================

import customtkinter as ctk
from tkinter import ttk
from datetime import date, timedelta
from utils import run_async, format_date


class ReadersTab:
    def __init__(self, parent, client):
        self.client = client
        self.parent = parent

        ctk.CTkLabel(parent, text="Читатели", font=("Segoe UI", 18, "bold"),
                     text_color="#24292f").pack(pady=(10, 5))

        # Фильтры
        filter_frame = ctk.CTkFrame(parent, corner_radius=10, fg_color="white",
                                    border_width=1, border_color="#d0d7de")
        filter_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filter_frame, text="Фамилия:", text_color="#24292f", font=("Segoe UI", 14)).pack(side="left", padx=(12, 4), pady=10)
        self.entry_last = ctk.CTkEntry(filter_frame, width=140, height=32, font=("Segoe UI", 15), border_color="#d0d7de")
        self.entry_last.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(filter_frame, text="Билет:", text_color="#24292f", font=("Segoe UI", 14)).pack(side="left", padx=(8, 4), pady=10)
        self.entry_card = ctk.CTkEntry(filter_frame, width=90, height=32, font=("Segoe UI", 15), border_color="#d0d7de")
        self.entry_card.pack(side="left", padx=4, pady=10)

        ctk.CTkButton(filter_frame, text="Найти", width=65, height=32, font=("Segoe UI", 15, "bold"), command=self._search).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(filter_frame, text="Сброс", width=55, height=32, font=("Segoe UI", 15, "bold"), command=self._load).pack(side="left", padx=4, pady=10)

        # Таблица
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("id", "full_name", "phone", "issue_date", "expiration_date")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=12)
        self.tree.heading("id", text="№ билета", command=lambda: self._sort_column("id"))
        self.tree.heading("full_name", text="ФИО", command=lambda: self._sort_column("full_name"))
        self.tree.heading("phone", text="Телефон", command=lambda: self._sort_column("phone"))
        self.tree.heading("issue_date", text="Выдан", command=lambda: self._sort_column("issue_date"))
        self.tree.heading("expiration_date", text="Действует до", command=lambda: self._sort_column("expiration_date"))

        self.tree.column("id", anchor="center")
        self.tree.column("full_name")
        self.tree.column("phone")
        self.tree.column("issue_date", anchor="center")
        self.tree.column("expiration_date", anchor="center")
        from utils import bind_tree_columns
        bind_tree_columns(self.tree, {
            "id": 0.10, "full_name": 0.35, "phone": 0.20,
            "issue_date": 0.175, "expiration_date": 0.175
        })

        scroll = ctk.CTkScrollbar(card, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.tree.tag_configure("expired", foreground="#c62828")
        self.tree.tag_configure("even", background="#f6f8fa")

        # Кнопки
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Добавить", command=self._add_reader,
                      width=120, height=38, font=("Segoe UI", 14, "bold"),
                      fg_color="#2e7d32", hover_color="#1b5e20").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Редактировать", command=self._edit_reader,
                      width=140, height=38, font=("Segoe UI", 14, "bold"),
                      fg_color="#1565c0", hover_color="#0d47a1").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Продлить", command=self._renew,
                      width=110, height=38, font=("Segoe UI", 14, "bold"),
                      fg_color="#e65100", hover_color="#bf360c").pack(side="left", padx=5)

        # Статус-бар
        self.status_label = ctk.CTkLabel(parent, text="", font=("Segoe UI", 14))
        self.status_label.pack(fill="x", padx=10, pady=(0, 5))

        self._load()

    def _show_status(self, text, color="gray"):
        self.status_label.configure(text=text, text_color=color)
        self.parent.after(5000, lambda: self.status_label.configure(text=""))

    def _format_fio(self, r: dict) -> str:
        parts = [
            r.get("last_name", ""),
            r.get("first_name", ""),
            (r.get("middle_name") or "")
        ]
        return " ".join(p for p in parts if p).strip()

    def _sort_column(self, col):
        from utils import sort_treeview
        reverse = getattr(self, "_sort_reverse", {}).get(col, False)
        sort_treeview(self.tree, col, reverse)
        self._sort_reverse = getattr(self, "_sort_reverse", {})
        self._sort_reverse[col] = not reverse

    def _load(self):
        self.entry_last.delete(0, "end")
        self.entry_card.delete(0, "end")

        def fetch():
            return self.client.get("/readers")

        def on_success(readers):
            self._fill_tree(readers)

        def on_error(e):
            self._show_status(f"Ошибка загрузки: {e}", "#c62828")

        run_async(self.parent, fetch, on_success, on_error)

    def _search(self):
        last = self.entry_last.get().strip().lower()
        card = self.entry_card.get().strip()

        def fetch():
            return self.client.get("/readers")

        def on_success(readers):
            filtered = []
            for r in readers:
                fio = self._format_fio(r).lower()
                if last and last not in fio:
                    continue
                if card and card not in str(r.get("id", "")):
                    continue
                filtered.append(r)
            self._fill_tree(filtered)

        def on_error(e):
            self._show_status(f"Ошибка: {e}", "#c62828")

        run_async(self.parent, fetch, on_success, on_error)

    def _fill_tree(self, readers):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, r in enumerate(readers):
            fio = self._format_fio(r)
            exp = r.get("expiration_date")
            tag = ""
            if exp and date.fromisoformat(exp) < date.today():
                tag = "expired"
            if i % 2 == 0:
                tag = (tag, "even") if tag else "even"
            self.tree.insert("", "end", values=(
                r.get("id"), fio, r.get("phone"),
                format_date(r.get("issue_date", "")),
                format_date(r.get("expiration_date", ""))
            ), tags=tag if isinstance(tag, str) else tag)

    def _add_reader(self):
        dlg = ctk.CTkToplevel(self.parent)
        dlg.title("Новый читатель")
        dlg.grab_set()
        dlg.configure(fg_color="#f0f2f5")
        dlg.transient(self.parent)
        dlg.withdraw()
        from utils import center_dialog
        def _place():
            center_dialog(dlg, 460, None, resizable=True)
            dlg.deiconify()
        dlg.after(100, _place)

        card = ctk.CTkFrame(dlg, corner_radius=12, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(card, text="Регистрация читателя",
                     font=("Segoe UI", 20, "bold"), text_color="#24292f").pack(pady=(15, 12))

        frame = ctk.CTkFrame(card, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=5)

        fields = [
            ("Фамилия *", "last_name"),
            ("Имя *", "first_name"),
            ("Отчество", "middle_name"),
            ("Телефон", "phone"),
        ]
        from utils import add_live_validation_with_hint, validate_name, validate_phone
        self._reader_entries = {}
        self._reader_hints = {}
        for label_text, key in fields:
            lbl_row = ctk.CTkFrame(frame, fg_color="transparent")
            lbl_row.pack(fill="x", pady=(2, 0))
            ctk.CTkLabel(lbl_row, text=label_text, font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
            hint = ctk.CTkLabel(lbl_row, text="", font=("Segoe UI", 11), text_color="#c62828")
            hint.pack(side="left", padx=(6, 0))
            ent = ctk.CTkEntry(frame, width=380, height=36, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
            ent.pack(fill="x", pady=(0, 4))
            if key == "phone":
                add_live_validation_with_hint(ent, validate_phone, hint)
            elif key in ("last_name", "first_name"):
                add_live_validation_with_hint(ent, lambda v, lt=label_text: validate_name(v, lt.replace(" *", "")), hint)
            elif key == "middle_name":
                add_live_validation_with_hint(ent, lambda v: validate_name(v, "Отчество", required=False), hint)
            self._reader_entries[key] = ent
            self._reader_hints[key] = hint

        ctk.CTkLabel(frame, text="Действует до (ДД.ММ.ГГГГ) *", font=("Segoe UI", 15), text_color="#24292f").pack(anchor="w", pady=(4, 0))
        ent_exp = ctk.CTkEntry(frame, width=380, height=36, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_exp.insert(0, (date.today() + timedelta(days=365)).strftime("%d.%m.%Y"))
        ent_exp.pack(fill="x", pady=(0, 4))
        self._reader_entries["expiration_date"] = ent_exp

        error_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 14), text_color="#c62828")
        error_label.pack(pady=(4, 0))

        def save():
            ln = self._reader_entries["last_name"].get().strip()
            fn = self._reader_entries["first_name"].get().strip()
            mn = self._reader_entries["middle_name"].get().strip() or None
            phone = self._reader_entries["phone"].get().strip() or None
            from utils import validate_name, validate_phone
            for err in [validate_name(ln, "Фамилия"), validate_name(fn, "Имя"),
                        validate_name(mn or "", "Отчество", required=False),
                        validate_phone(phone)]:
                if err:
                    error_label.configure(text=err)
                    return
            data = {
                "last_name": ln, "first_name": fn,
                "middle_name": self._reader_entries["middle_name"].get().strip() or None,
                "phone": self._reader_entries["phone"].get().strip() or None,
                "expiration_date": self._reader_entries["expiration_date"].get().strip(),
            }
            from utils import validate_date_str
            exp_err = validate_date_str(data["expiration_date"], "Действует до")
            if exp_err:
                error_label.configure(text=exp_err)
                return

            def do_post():
                return self.client.post("/readers", data)

            def on_ok(_):
                dlg.after(50, dlg.destroy)
                self._show_status("Читатель зарегистрирован", "#2e7d32")
                self._load()

            def on_err(e):
                error_label.configure(text=str(e))

            run_async(dlg, do_post, on_ok, on_err)

        ctk.CTkButton(card, text="Сохранить", command=save,
                      width=200, height=42, font=("Segoe UI", 15, "bold"),
                      fg_color="#2e7d32", hover_color="#1b5e20").pack(pady=6)

    def _edit_reader(self):
        sel = self.tree.selection()
        if not sel:
            self._show_status("Выберите читателя", "#c62828")
            return
        values = self.tree.item(sel[0], "values")
        card_id = values[0]
        current_fio = values[1]
        current_phone = values[2]

        # Получаем полные данные с сервера для редактирования
        def fetch():
            return self.client.get(f"/readers/{card_id}")

        def on_load(reader):
            dlg = ctk.CTkToplevel(self.parent)
            dlg.title("Редактирование читателя")
            dlg.grab_set()
            dlg.configure(fg_color="#f0f2f5")
            dlg.transient(self.parent)
            dlg.withdraw()
            from utils import center_dialog
            def _place():
                center_dialog(dlg, 460, None, resizable=True)
                dlg.deiconify()
            dlg.after(100, _place)

            card = ctk.CTkFrame(dlg, corner_radius=12, fg_color="white",
                                border_width=1, border_color="#d0d7de")
            card.pack(fill="x", padx=10, pady=10)

            ctk.CTkLabel(card, text="Редактирование читателя",
                         font=("Segoe UI", 20, "bold"), text_color="#24292f").pack(pady=(15, 12))

            frame = ctk.CTkFrame(card, fg_color="transparent")
            frame.pack(fill="x", padx=12, pady=5)

            fields = [
                ("Фамилия *", "last_name", reader.get("last_name", "")),
                ("Имя *", "first_name", reader.get("first_name", "")),
                ("Отчество", "middle_name", reader.get("middle_name", "")),
                ("Телефон", "phone", reader.get("phone", "")),
            ]
            from utils import add_live_validation_with_hint, validate_name, validate_phone
            entries = {}
            for label_text, key, val in fields:
                lbl_row = ctk.CTkFrame(frame, fg_color="transparent")
                lbl_row.pack(fill="x", pady=(2, 0))
                ctk.CTkLabel(lbl_row, text=label_text, font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
                hint = ctk.CTkLabel(lbl_row, text="", font=("Segoe UI", 11), text_color="#c62828")
                hint.pack(side="left", padx=(6, 0))
                ent = ctk.CTkEntry(frame, width=380, height=36, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
                ent.insert(0, val or "")
                ent.pack(fill="x", pady=(0, 4))
                if key == "phone":
                    add_live_validation_with_hint(ent, validate_phone, hint)
                elif key in ("last_name", "first_name"):
                    add_live_validation_with_hint(ent, lambda v, lt=label_text: validate_name(v, lt.replace(" *", "")), hint)
                elif key == "middle_name":
                    add_live_validation_with_hint(ent, lambda v: validate_name(v, "Отчество", required=False), hint)
                entries[key] = ent

            error_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 14), text_color="#c62828")
            error_label.pack(pady=(4, 0))

            def save():
                ln = entries["last_name"].get().strip()
                fn = entries["first_name"].get().strip()
                mn = entries["middle_name"].get().strip() or None
                phone = entries["phone"].get().strip() or None
                from utils import validate_name, validate_phone
                for err in [validate_name(ln, "Фамилия"), validate_name(fn, "Имя"),
                            validate_name(mn or "", "Отчество", required=False),
                            validate_phone(phone)]:
                    if err:
                        error_label.configure(text=err)
                        return
                data = {
                    "last_name": ln, "first_name": fn,
                    "middle_name": entries["middle_name"].get().strip() or None,
                    "phone": entries["phone"].get().strip() or None,
                }

                def do_patch():
                    return self.client.patch(f"/readers/{card_id}", data)

                def on_ok(_):
                    dlg.after(50, dlg.destroy)
                    self._show_status("Данные читателя обновлены", "#2e7d32")
                    self._load()

                def on_err(e):
                    error_label.configure(text=str(e))

                run_async(dlg, do_patch, on_ok, on_err)

            ctk.CTkButton(card, text="Сохранить изменения", command=save,
                          width=200, height=42, font=("Segoe UI", 15, "bold"),
                          fg_color="#1565c0", hover_color="#0d47a1").pack(pady=6)

        def on_err(e):
            self._show_status(f"Ошибка загрузки: {e}", "#c62828")

        from utils import run_async
        run_async(self.parent, fetch, on_load, on_err)

    def _renew(self):
        sel = self.tree.selection()
        if not sel:
            self._show_status("Выберите читателя", "#c62828")
            return
        card_id = self.tree.item(sel[0], "values")[0]

        dlg = ctk.CTkToplevel(self.parent)
        dlg.title("Продление билета")
        dlg.grab_set()
        dlg.configure(fg_color="#f0f2f5")
        dlg.transient(self.parent)
        dlg.withdraw()
        from utils import center_dialog
        def _place():
            center_dialog(dlg, 380, None, resizable=True)
            dlg.deiconify()
        dlg.after(100, _place)

        card = ctk.CTkFrame(dlg, corner_radius=12, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(card, text="Продление билета",
                     font=("Segoe UI", 18, "bold"), text_color="#24292f").pack(pady=(15, 10))

        ctk.CTkLabel(card, text="Новая дата окончания (ДД.ММ.ГГГГ)",
                     font=("Segoe UI", 15), text_color="#24292f").pack(pady=5)
        ent = ctk.CTkEntry(card, width=300, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent.insert(0, (date.today() + timedelta(days=365)).strftime("%d.%m.%Y"))
        ent.pack(fill="x", padx=12, pady=5)

        error_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 14), text_color="#c62828")
        error_label.pack()

        def do_renew():
            from utils import validate_date_str
            date_err = validate_date_str(ent.get().strip(), "Новая дата окончания")
            if date_err:
                error_label.configure(text=date_err)
                return
            def post():
                return self.client.post(f"/readers/{card_id}/renew", {"expiration_date": ent.get().strip()})

            def on_ok(_):
                dlg.after(50, dlg.destroy)
                self._show_status("Билет продлен", "#2e7d32")
                self._load()

            def on_err(e):
                error_label.configure(text=str(e))

            run_async(dlg, post, on_ok, on_err)

        ctk.CTkButton(card, text="Продлить", command=do_renew,
                      width=150, height=40, font=("Segoe UI", 14, "bold"),
                      fg_color="#1565c0", hover_color="#0d47a1").pack(pady=12)
