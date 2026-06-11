# ============================================================
# Вкладка "Аренда"
# ============================================================

import customtkinter as ctk
from tkinter import ttk
from datetime import date, timedelta
from utils import run_async, format_date


class RentalsTab:
    def __init__(self, parent, client):
        self.client = client
        self.parent = parent

        ctk.CTkLabel(parent, text="Аренда книг", font=("Segoe UI", 18, "bold"),
                     text_color="#24292f").pack(pady=(10, 5))

        # Фильтры
        filter_frame = ctk.CTkFrame(parent, corner_radius=10, fg_color="white",
                                    border_width=1, border_color="#d0d7de")
        filter_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filter_frame, text="Статус:", text_color="#24292f", font=("Segoe UI", 14)).pack(side="left", padx=(12, 4), pady=10)
        self.combo_status = ctk.CTkComboBox(filter_frame, values=["Все", "Активные", "Возвращённые", "Просроченные"], width=120, height=32, font=("Segoe UI", 15))
        self.combo_status.pack(side="left", padx=4, pady=10)
        self.combo_status.set("Все")

        ctk.CTkLabel(filter_frame, text="Читатель:", text_color="#24292f", font=("Segoe UI", 14)).pack(side="left", padx=(8, 4), pady=10)
        self.entry_fio = ctk.CTkEntry(filter_frame, width=140, height=32, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        self.entry_fio.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(filter_frame, text="№ билета:", text_color="#24292f", font=("Segoe UI", 14)).pack(side="left", padx=(8, 4), pady=10)
        self.entry_card = ctk.CTkEntry(filter_frame, width=100, height=32, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        self.entry_card.pack(side="left", padx=4, pady=10)

        ctk.CTkButton(filter_frame, text="Применить", width=90, height=32, font=("Segoe UI", 15, "bold"), command=self._load).pack(side="left", padx=8, pady=10)

        # Таблица
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("id", "book_title", "reader_name", "issue_date", "due_date", "actual_return", "status", "fine")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=12)
        self.tree.heading("id", text="№ операции", command=lambda: self._sort_column("id"))
        self.tree.heading("book_title", text="Книга", command=lambda: self._sort_column("book_title"))
        self.tree.heading("reader_name", text="Читатель", command=lambda: self._sort_column("reader_name"))
        self.tree.heading("issue_date", text="Выдана", command=lambda: self._sort_column("issue_date"))
        self.tree.heading("due_date", text="Вернуть до", command=lambda: self._sort_column("due_date"))
        self.tree.heading("actual_return", text="Дата возврата", command=lambda: self._sort_column("actual_return"))
        self.tree.heading("status", text="Статус", command=lambda: self._sort_column("status"))
        self.tree.heading("fine", text="Штраф", command=lambda: self._sort_column("fine"))

        self.tree.column("id", anchor="center")
        self.tree.column("book_title")
        self.tree.column("reader_name")
        self.tree.column("issue_date", anchor="center")
        self.tree.column("due_date", anchor="center")
        self.tree.column("actual_return", anchor="center")
        self.tree.column("status", anchor="center")
        self.tree.column("fine", anchor="center")
        from utils import bind_tree_columns
        bind_tree_columns(self.tree, {
            "id": 0.07, "book_title": 0.22, "reader_name": 0.17,
            "issue_date": 0.10, "due_date": 0.10, "actual_return": 0.10,
            "status": 0.12, "fine": 0.12
        })

        scroll = ctk.CTkScrollbar(card, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.tree.tag_configure("overdue", foreground="#c62828")
        self.tree.tag_configure("even", background="#f6f8fa")

        # Кнопки
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Выдать книгу", command=self._issue,
                      width=130, height=38, font=("Segoe UI", 14, "bold"),
                      fg_color="#2e7d32", hover_color="#1b5e20").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Вернуть", command=self._return,
                      width=110, height=38, font=("Segoe UI", 14, "bold"),
                      fg_color="#1565c0", hover_color="#0d47a1").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Продлить", command=self._extend,
                      width=110, height=38, font=("Segoe UI", 14, "bold"),
                      fg_color="#e65100", hover_color="#bf360c").pack(side="left", padx=5)

        # Статус-бар
        self.status_label = ctk.CTkLabel(parent, text="", font=("Segoe UI", 14))
        self.status_label.pack(fill="x", padx=10, pady=(0, 5))

        self._load()

    def _sort_column(self, col):
        from utils import sort_treeview
        reverse = getattr(self, "_sort_reverse", {}).get(col, False)
        sort_treeview(self.tree, col, reverse)
        self._sort_reverse = getattr(self, "_sort_reverse", {})
        self._sort_reverse[col] = not reverse

    def _show_status(self, text, color="gray"):
        self.status_label.configure(text=text, text_color=color)
        self.parent.after(5000, lambda: self.status_label.configure(text=""))

    def _load(self):
        def fetch():
            mode = self.combo_status.get()
            if mode == "Активные":
                rentals = self.client.get("/rentals/active")
            else:
                rentals = self.client.get("/rentals")
            if mode == "Возвращённые":
                rentals = [r for r in rentals if r.get("actual_return_date")]
            elif mode == "Просроченные":
                today = date.today()
                rentals = [r for r in rentals if not r.get("actual_return_date") and r.get("due_date") and date.fromisoformat(r.get("due_date")) < today]
            # Фильтрация по ФИО и номеру билета (на клиенте)
            fio_filter = self.entry_fio.get().strip().lower()
            card_filter = self.entry_card.get().strip()
            if fio_filter:
                rentals = [r for r in rentals if fio_filter in (r.get("reader_name") or "").lower()]
            if card_filter:
                rentals = [r for r in rentals if card_filter in (r.get("reader_card_id") or "")]
            return rentals

        def on_success(rentals):
            self._fill_tree(rentals)

        def on_error(e):
            self._show_status(f"Ошибка загрузки: {e}", "#c62828")

        run_async(self.parent, fetch, on_success, on_error)

    def _fill_tree(self, rentals):
        for item in self.tree.get_children():
            self.tree.delete(item)
        today = date.today()
        for i, r in enumerate(rentals):
            actual = r.get("actual_return_date")
            # Динамически определяем просрочку для активных аренд
            is_overdue = r.get("is_overdue", False)
            due = r.get("due_date")
            if due and not actual:
                try:
                    if date.fromisoformat(due) < today:
                        is_overdue = True
                except Exception:
                    pass
            status = "Возвращена" if actual else ("Просрочена" if is_overdue else "Активна")
            tag = ""
            if is_overdue and not actual:
                tag = "overdue"
            if i % 2 == 0:
                tag = (tag, "even") if tag else "even"
            fine = r.get("fine_amount", 0) or 0
            # Динамически считаем штраф для активных просроченных аренд
            if is_overdue and not actual:
                try:
                    fine = (today - date.fromisoformat(due)).days * 10.0
                except Exception:
                    fine = 0
            self.tree.insert("", "end", values=(
                r.get("id"), r.get("book_title", ""), r.get("reader_name", ""),
                format_date(r.get("issue_date", "")),
                format_date(r.get("due_date", "")),
                format_date(r.get("actual_return_date", "")),
                status, f"{fine:.2f}"
            ), tags=tag if isinstance(tag, str) else tag)

    def _issue(self):
        dlg = ctk.CTkToplevel(self.parent)
        dlg.title("Выдача книги")
        dlg.grab_set()
        dlg.configure(fg_color="#f0f2f5")
        dlg.transient(self.parent)
        dlg.withdraw()
        from utils import center_dialog
        def _place():
            center_dialog(dlg, 420, None, resizable=True)
            dlg.deiconify()
        dlg.after(100, _place)

        card = ctk.CTkFrame(dlg, corner_radius=12, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(card, text="Выдача книги",
                     font=("Segoe UI", 20, "bold"), text_color="#24292f").pack(pady=(12, 10))

        frame = ctk.CTkFrame(card, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=5)

        from utils import add_live_validation_with_hint, validate_positive_int, validate_reader_card_id
        lbl_row_book = ctk.CTkFrame(frame, fg_color="transparent")
        lbl_row_book.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(lbl_row_book, text="Инв. № книги *", font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
        hint_book = ctk.CTkLabel(lbl_row_book, text="", font=("Segoe UI", 11), text_color="#c62828")
        hint_book.pack(side="left", padx=(6, 0))
        ent_book = ctk.CTkEntry(frame, width=340, height=36, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_book.pack(fill="x", pady=(0, 4))
        add_live_validation_with_hint(ent_book, lambda v: validate_positive_int(v, "№ книги"), hint_book)

        lbl_row_card = ctk.CTkFrame(frame, fg_color="transparent")
        lbl_row_card.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(lbl_row_card, text="№ читательского билета *", font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
        hint_card = ctk.CTkLabel(lbl_row_card, text="", font=("Segoe UI", 11), text_color="#c62828")
        hint_card.pack(side="left", padx=(6, 0))
        ent_card = ctk.CTkEntry(frame, width=340, height=36, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_card.pack(fill="x", pady=(0, 4))
        add_live_validation_with_hint(ent_card, validate_reader_card_id, hint_card)

        lbl_row_days = ctk.CTkFrame(frame, fg_color="transparent")
        lbl_row_days.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(lbl_row_days, text="Срок (дней)", font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
        hint_days = ctk.CTkLabel(lbl_row_days, text="", font=("Segoe UI", 11), text_color="#c62828")
        hint_days.pack(side="left", padx=(6, 0))
        ent_days = ctk.CTkEntry(frame, width=340, height=36, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_days.insert(0, "14")
        ent_days.pack(fill="x", pady=(0, 4))
        add_live_validation_with_hint(ent_days, lambda v: validate_positive_int(v, "Срок аренды"), hint_days)

        error_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 14), text_color="#c62828")
        error_label.pack(pady=(3, 0))

        def save():
            from utils import validate_positive_int, validate_reader_card_id
            book_id_str = ent_book.get().strip()
            card_id = ent_card.get().strip()
            days_str = ent_days.get().strip() or "14"
            for err in [validate_positive_int(book_id_str, "№ книги"),
                        validate_reader_card_id(card_id),
                        validate_positive_int(days_str, "Срок аренды")]:
                if err:
                    error_label.configure(text=err)
                    return
            data = {
                "book_id": int(book_id_str),
                "reader_card_id": card_id,
                "duration_days": int(days_str),
            }

            def do_post():
                return self.client.post("/rentals", data)

            def on_ok(_):
                dlg.after(50, dlg.destroy)
                self._show_status("Книга выдана", "#2e7d32")
                self._load()

            def on_err(e):
                msg = str(e) if e else "Неизвестная ошибка"
                error_label.configure(text=msg)

            run_async(dlg, do_post, on_ok, on_err)

        ctk.CTkButton(card, text="Выдать", command=save,
                      width=160, height=42, font=("Segoe UI", 15, "bold"),
                      fg_color="#2e7d32", hover_color="#1b5e20").pack(pady=6)

        ent_book.focus()
        dlg.bind("<Return>", lambda e: save())

    def _return(self):
        sel = self.tree.selection()
        if not sel:
            self._show_status("Выберите аренду", "#c62828")
            return
        values = self.tree.item(sel[0], "values")
        status = values[5]
        if status == "Возвращена":
            self._show_status("Книга уже возвращена", "#c62828")
            return
        rental_id = values[0]

        dlg = ctk.CTkToplevel(self.parent)
        dlg.title("Возврат книги")
        dlg.grab_set()
        dlg.configure(fg_color="#f0f2f5")
        dlg.transient(self.parent)
        dlg.withdraw()
        from utils import center_dialog
        def _place():
            center_dialog(dlg, 350, None, resizable=True)
            dlg.deiconify()
        dlg.after(100, _place)

        card = ctk.CTkFrame(dlg, corner_radius=12, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(card, text="Возврат книги",
                     font=("Segoe UI", 18, "bold"), text_color="#24292f").pack(pady=(12, 8))

        ctk.CTkLabel(card, text=f"Аренда #{rental_id}",
                     font=("Segoe UI", 14), text_color="#57606a").pack()

        ctk.CTkLabel(card, text="Дата возврата (ДД.ММ.ГГГГ)",
                     font=("Segoe UI", 15), text_color="#24292f").pack(pady=(8, 0))
        ent_date = ctk.CTkEntry(card, width=280, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_date.insert(0, date.today().strftime("%d.%m.%Y"))
        ent_date.pack(fill="x", padx=12, pady=4)

        error_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 14), text_color="#c62828")
        error_label.pack()

        def do_return():
            from datetime import datetime
            try:
                return_date = datetime.strptime(ent_date.get().strip(), "%d.%m.%Y").date()
            except ValueError:
                error_label.configure(text="Неверный формат даты (ДД.ММ.ГГГГ)")
                return

            def post():
                return self.client.post(f"/rentals/{rental_id}/return", {"return_date": return_date.strftime("%d.%m.%Y")})

            def on_ok(result):
                fine = result.get("fine", 0)
                if fine > 0:
                    self._show_status(f"Возврат оформлен. Штраф: {fine:.2f} руб.", "#e65100")
                else:
                    self._show_status("Книга возвращена", "#2e7d32")
                dlg.after(50, dlg.destroy)
                self._load()

            def on_err(e):
                msg = str(e) if e else "Неизвестная ошибка"
                error_label.configure(text=msg)

            run_async(dlg, post, on_ok, on_err)

        ctk.CTkButton(card, text="Подтвердить возврат", command=do_return,
                      width=180, height=40, font=("Segoe UI", 14, "bold"),
                      fg_color="#1565c0", hover_color="#0d47a1").pack(pady=10)

    def _extend(self):
        sel = self.tree.selection()
        if not sel:
            self._show_status("Выберите аренду", "#c62828")
            return
        values = self.tree.item(sel[0], "values")
        status = values[5]
        if status == "Возвращена":
            self._show_status("Нельзя продлить возвращённую книгу", "#c62828")
            return
        rental_id = values[0]

        dlg = ctk.CTkToplevel(self.parent)
        dlg.title("Продление аренды")
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

        ctk.CTkLabel(card, text="Продление аренды",
                     font=("Segoe UI", 18, "bold"), text_color="#24292f").pack(pady=(12, 8))

        ctk.CTkLabel(card, text="Новая дата возврата (ДД.ММ.ГГГГ)",
                     font=("Segoe UI", 15), text_color="#24292f").pack(pady=4)
        ent = ctk.CTkEntry(card, width=300, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent.insert(0, (date.today() + timedelta(days=14)).strftime("%d.%m.%Y"))
        ent.pack(fill="x", padx=12, pady=4)

        error_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 14), text_color="#c62828")
        error_label.pack()

        def do_extend():
            from utils import validate_date_str
            date_err = validate_date_str(ent.get().strip(), "Новая дата возврата")
            if date_err:
                error_label.configure(text=date_err)
                return
            def post():
                return self.client.post(f"/rentals/{rental_id}/extend", {"new_due_date": ent.get().strip()})

            def on_ok(_):
                dlg.after(50, dlg.destroy)
                self._show_status("Аренда продлена", "#2e7d32")
                self._load()

            def on_err(e):
                msg = str(e) if e else "Неизвестная ошибка"
                error_label.configure(text=msg)

            run_async(dlg, post, on_ok, on_err)

        ctk.CTkButton(card, text="Продлить", command=do_extend,
                      width=150, height=40, font=("Segoe UI", 14, "bold"),
                      fg_color="#e65100", hover_color="#bf360c").pack(pady=10)
