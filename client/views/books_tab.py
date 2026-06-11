# ============================================================
# Вкладка "Каталог"
# ============================================================

import customtkinter as ctk
from tkinter import ttk
from utils import run_async


class BooksTab:
    def __init__(self, parent, client):
        self.client = client
        self.parent = parent
        self.genres_list = [""]

        ctk.CTkLabel(parent, text="Каталог книг", font=("Segoe UI", 18, "bold"),
                     text_color="#24292f").pack(pady=(10, 5))

        # Фильтры
        filter_frame = ctk.CTkFrame(parent, corner_radius=10, fg_color="white",
                                    border_width=1, border_color="#d0d7de")
        filter_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filter_frame, text="Автор:", text_color="#24292f", font=("Segoe UI", 14)).pack(side="left", padx=(12, 4), pady=10)
        self.entry_author = ctk.CTkEntry(filter_frame, width=95, height=32, font=("Segoe UI", 15), border_color="#d0d7de")
        self.entry_author.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(filter_frame, text="Название:", text_color="#24292f", font=("Segoe UI", 14)).pack(side="left", padx=(8, 4), pady=10)
        self.entry_title = ctk.CTkEntry(filter_frame, width=95, height=32, font=("Segoe UI", 15), border_color="#d0d7de")
        self.entry_title.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(filter_frame, text="Жанр:", text_color="#24292f", font=("Segoe UI", 14)).pack(side="left", padx=(8, 4), pady=10)
        self.combo_genre = ctk.CTkComboBox(filter_frame, values=self.genres_list, width=95, height=32, font=("Segoe UI", 15))
        self.combo_genre.pack(side="left", padx=4, pady=10)
        self.combo_genre.set("")

        ctk.CTkLabel(filter_frame, text="ISBN:", text_color="#24292f", font=("Segoe UI", 14)).pack(side="left", padx=(8, 4), pady=10)
        self.entry_isbn = ctk.CTkEntry(filter_frame, width=85, height=32, font=("Segoe UI", 15), border_color="#d0d7de")
        self.entry_isbn.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(filter_frame, text="Год:", text_color="#24292f", font=("Segoe UI", 14)).pack(side="left", padx=(8, 4), pady=10)
        self.entry_year = ctk.CTkEntry(filter_frame, width=55, height=32, font=("Segoe UI", 15), border_color="#d0d7de")
        self.entry_year.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(filter_frame, text="Статус:", text_color="#24292f", font=("Segoe UI", 14)).pack(side="left", padx=(8, 4), pady=10)
        self.combo_status = ctk.CTkComboBox(filter_frame, values=["", "В наличии", "Выдана", "Утрачена"],
                                            width=90, height=32, font=("Segoe UI", 15))
        self.combo_status.pack(side="left", padx=4, pady=10)
        self.combo_status.set("")

        ctk.CTkButton(filter_frame, text="Найти", width=65, height=32, font=("Segoe UI", 15, "bold"), command=self._search).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(filter_frame, text="Сброс", width=55, height=32, font=("Segoe UI", 15, "bold"), command=self._load).pack(side="left", padx=4, pady=10)

        # Таблица
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("id", "title", "author", "year", "genre", "isbn", "location", "status")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=12)
        self.tree.heading("id", text="Инв. №", command=lambda: self._sort_column("id"))
        self.tree.heading("title", text="Название", command=lambda: self._sort_column("title"))
        self.tree.heading("author", text="Автор", command=lambda: self._sort_column("author"))
        self.tree.heading("year", text="Год", command=lambda: self._sort_column("year"))
        self.tree.heading("genre", text="Жанр", command=lambda: self._sort_column("genre"))
        self.tree.heading("isbn", text="ISBN", command=lambda: self._sort_column("isbn"))
        self.tree.heading("location", text="Место", command=lambda: self._sort_column("location"))
        self.tree.heading("status", text="Статус", command=lambda: self._sort_column("status"))

        self.tree.column("id", anchor="center")
        self.tree.column("title")
        self.tree.column("author")
        self.tree.column("year", anchor="center")
        self.tree.column("genre")
        self.tree.column("isbn")
        self.tree.column("location")
        self.tree.column("status", anchor="center")
        from utils import bind_tree_columns
        bind_tree_columns(self.tree, {
            "id": 0.06, "title": 0.24, "author": 0.15, "year": 0.07,
            "genre": 0.12, "isbn": 0.13, "location": 0.11, "status": 0.12
        })

        scroll = ctk.CTkScrollbar(card, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.tree.tag_configure("available", background="#e8f5e9", foreground="#1b5e20")
        self.tree.tag_configure("rented", background="#fff3e0", foreground="#e65100")
        self.tree.tag_configure("lost", background="#fce4ec", foreground="#b71c1c")
        self.tree.tag_configure("even", background="#f6f8fa")

        # Кнопки
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Добавить книгу", command=self._add_book,
                      width=140, height=38, font=("Segoe UI", 14, "bold"),
                      fg_color="#2e7d32", hover_color="#1b5e20").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Редактировать", command=self._edit_book,
                      width=140, height=38, font=("Segoe UI", 14, "bold"),
                      fg_color="#1565c0", hover_color="#0d47a1").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Удалить", command=self._delete_book,
                      width=110, height=38, font=("Segoe UI", 14, "bold"),
                      fg_color="#c62828", hover_color="#b71c1c").pack(side="left", padx=5)

        # Статус-бар
        self.status_label = ctk.CTkLabel(parent, text="", font=("Segoe UI", 14))
        self.status_label.pack(fill="x", padx=10, pady=(0, 5))

        self._load()
        self._load_genres()

    def _show_status(self, text, color="gray"):
        self.status_label.configure(text=text, text_color=color)
        self.parent.after(5000, lambda: self.status_label.configure(text=""))

    def _load_genres(self):
        def fetch():
            return self.client.get("/genres")

        def on_success(genres):
            names = [""] + [g.get("name", "") for g in genres]
            self.genres_list = names
            self.combo_genre.configure(values=names)

        def on_error(e):
            pass

        run_async(self.parent, fetch, on_success, on_error)

    def _load(self):
        self._clear_entries()

        def fetch():
            return self.client.get("/books")

        def on_success(books):
            self._fill_tree(books)

        def on_error(e):
            self._show_status(f"Ошибка загрузки: {e}", "#c62828")

        run_async(self.parent, fetch, on_success, on_error)

    def _search(self):
        filters = {}
        if self.entry_author.get().strip():
            filters["author"] = self.entry_author.get().strip()
        if self.entry_title.get().strip():
            filters["title"] = self.entry_title.get().strip()
        if self.entry_isbn.get().strip():
            filters["isbn"] = self.entry_isbn.get().strip()
        if self.entry_year.get().strip():
            try:
                filters["year"] = int(self.entry_year.get().strip())
            except ValueError:
                self._show_status("Год должен быть числом", "#c62828")
                return
        if self.combo_genre.get():
            filters["genre"] = self.combo_genre.get()
        if self.combo_status.get():
            filters["status"] = self.combo_status.get()

        def fetch():
            return self.client.post("/books/search", filters)

        def on_success(books):
            self._fill_tree(books)

        def on_error(e):
            self._show_status(f"Ошибка: {e}", "#c62828")

        run_async(self.parent, fetch, on_success, on_error)

    def _fill_tree(self, books):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, b in enumerate(books):
            tag = ""
            status = b.get("status")
            if status == "В наличии":
                tag = "available"
            elif status == "Выдана":
                tag = "rented"
            elif status == "Утрачена":
                tag = "lost"
            if i % 2 == 0:
                tag = ("even", tag) if tag else "even"
            self.tree.insert("", "end", values=(
                b.get("id"), b.get("title"), b.get("author"),
                b.get("year"), b.get("genre"), (b.get("isbn") or "-"),
                b.get("location"), status
            ), tags=tag if isinstance(tag, str) else tag)

    def _sort_column(self, col):
        from utils import sort_treeview
        reverse = getattr(self, "_sort_reverse", {}).get(col, False)
        sort_treeview(self.tree, col, reverse)
        self._sort_reverse = getattr(self, "_sort_reverse", {})
        self._sort_reverse[col] = not reverse

    def _clear_entries(self):
        self.entry_author.delete(0, "end")
        self.entry_title.delete(0, "end")
        self.entry_isbn.delete(0, "end")
        self.entry_year.delete(0, "end")
        self.combo_genre.set("")
        self.combo_status.set("")

    def _add_book(self):
        dlg = ctk.CTkToplevel(self.parent)
        dlg.title("Добавить книгу")
        dlg.grab_set()
        dlg.configure(fg_color="#f0f2f5")
        dlg.transient(self.parent)
        dlg.withdraw()
        from utils import center_dialog
        def _place():
            center_dialog(dlg, 480, None, resizable=True)
            dlg.deiconify()
        dlg.after(100, _place)

        card = ctk.CTkFrame(dlg, corner_radius=12, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(card, text="Добавление книги",
                     font=("Segoe UI", 20, "bold"), text_color="#24292f").pack(pady=(15, 12))

        frame = ctk.CTkFrame(card, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=5)

        from utils import add_live_validation_with_hint, validate_year_str, validate_isbn
        ctk.CTkLabel(frame, text="Название *", font=("Segoe UI", 15), text_color="#24292f").pack(anchor="w", pady=(2, 0))
        ent_title = ctk.CTkEntry(frame, width=400, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_title.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(frame, text="Автор *", font=("Segoe UI", 15), text_color="#24292f").pack(anchor="w", pady=(2, 0))
        ent_author = ctk.CTkEntry(frame, width=400, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_author.pack(fill="x", pady=(0, 4))

        lbl_row_year = ctk.CTkFrame(frame, fg_color="transparent")
        lbl_row_year.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(lbl_row_year, text="Год издания", font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
        hint_year = ctk.CTkLabel(lbl_row_year, text="", font=("Segoe UI", 11), text_color="#c62828")
        hint_year.pack(side="left", padx=(6, 0))
        ent_year = ctk.CTkEntry(frame, width=400, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_year.pack(fill="x", pady=(0, 4))
        add_live_validation_with_hint(ent_year, validate_year_str, hint_year)

        lbl_row_isbn = ctk.CTkFrame(frame, fg_color="transparent")
        lbl_row_isbn.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(lbl_row_isbn, text="ISBN (13 цифр)", font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
        hint_isbn = ctk.CTkLabel(lbl_row_isbn, text="", font=("Segoe UI", 11), text_color="#c62828")
        hint_isbn.pack(side="left", padx=(6, 0))
        ent_isbn = ctk.CTkEntry(frame, width=400, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_isbn.pack(fill="x", pady=(0, 4))
        add_live_validation_with_hint(ent_isbn, validate_isbn, hint_isbn)

        ctk.CTkLabel(frame, text="Жанр", font=("Segoe UI", 15), text_color="#24292f").pack(anchor="w", pady=(2, 0))
        ent_genre = ctk.CTkComboBox(frame, values=self.genres_list, width=400, height=38, font=("Segoe UI", 14))
        ent_genre.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(frame, text="Место на полке", font=("Segoe UI", 15), text_color="#24292f").pack(anchor="w", pady=(2, 0))
        ent_loc = ctk.CTkEntry(frame, width=400, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_loc.pack(fill="x", pady=(0, 4))

        error_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 14), text_color="#c62828")
        error_label.pack(pady=(4, 0))

        def save():
            title = ent_title.get().strip()
            author = ent_author.get().strip()
            from utils import validate_required, validate_year_str, validate_isbn
            genre = ent_genre.get() or None
            if genre and genre not in self.genres_list:
                error_label.configure(text="Выберите жанр из списка")
                return
            for err in [validate_required(title, "Название"), validate_required(author, "Автор"),
                        validate_year_str(ent_year.get()), validate_isbn(ent_isbn.get())]:
                if err:
                    error_label.configure(text=err)
                    return
            data = {
                "title": title, "author": author,
                "year": int(ent_year.get()) if ent_year.get().strip() else None,
                "isbn": ent_isbn.get().strip() or None,
                "genre": genre,
                "location": ent_loc.get().strip() or None,
            }

            def do_post():
                return self.client.post("/books", data)

            def on_ok(_):
                dlg.after(50, dlg.destroy)
                self._show_status("Книга добавлена", "#2e7d32")
                self._load()

            def on_err(e):
                error_label.configure(text=str(e))

            run_async(dlg, do_post, on_ok, on_err)

        ctk.CTkButton(card, text="Сохранить", command=save,
                      width=200, height=42, font=("Segoe UI", 15, "bold"),
                      fg_color="#2e7d32", hover_color="#1b5e20").pack(pady=6)

    def _edit_book(self):
        sel = self.tree.selection()
        if not sel:
            self._show_status("Выберите книгу", "#c62828")
            return
        values = self.tree.item(sel[0], "values")
        book_id = values[0]
        current = {
            "title": values[1], "author": values[2], "year": values[3],
            "genre": values[4], "isbn": values[5], "location": values[6],
            "status": values[7],
        }

        dlg = ctk.CTkToplevel(self.parent)
        dlg.title("Редактирование книги")
        dlg.grab_set()
        dlg.configure(fg_color="#f0f2f5")
        dlg.transient(self.parent)
        dlg.withdraw()
        from utils import center_dialog
        def _place():
            center_dialog(dlg, 480, None, resizable=True)
            dlg.deiconify()
        dlg.after(100, _place)

        card = ctk.CTkFrame(dlg, corner_radius=12, fg_color="white",
                            border_width=1, border_color="#d0d7de")
        card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(card, text="Редактирование книги",
                     font=("Segoe UI", 20, "bold"), text_color="#24292f").pack(pady=(15, 12))

        frame = ctk.CTkFrame(card, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=5)

        from utils import add_live_validation_with_hint, validate_year_str, validate_isbn
        ctk.CTkLabel(frame, text="Название *", font=("Segoe UI", 15), text_color="#24292f").pack(anchor="w", pady=(3, 0))
        ent_title = ctk.CTkEntry(frame, width=400, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_title.insert(0, current["title"])
        ent_title.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(frame, text="Автор *", font=("Segoe UI", 15), text_color="#24292f").pack(anchor="w", pady=(3, 0))
        ent_author = ctk.CTkEntry(frame, width=400, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_author.insert(0, current["author"])
        ent_author.pack(fill="x", pady=(0, 4))

        lbl_row_year = ctk.CTkFrame(frame, fg_color="transparent")
        lbl_row_year.pack(fill="x", pady=(3, 0))
        ctk.CTkLabel(lbl_row_year, text="Год издания", font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
        hint_year = ctk.CTkLabel(lbl_row_year, text="", font=("Segoe UI", 11), text_color="#c62828")
        hint_year.pack(side="left", padx=(6, 0))
        ent_year = ctk.CTkEntry(frame, width=400, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_year.insert(0, str(current["year"]) if current["year"] else "")
        ent_year.pack(fill="x", pady=(0, 4))
        add_live_validation_with_hint(ent_year, validate_year_str, hint_year)

        lbl_row_isbn = ctk.CTkFrame(frame, fg_color="transparent")
        lbl_row_isbn.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(lbl_row_isbn, text="ISBN", font=("Segoe UI", 15), text_color="#24292f").pack(side="left")
        hint_isbn = ctk.CTkLabel(lbl_row_isbn, text="", font=("Segoe UI", 11), text_color="#c62828")
        hint_isbn.pack(side="left", padx=(6, 0))
        ent_isbn = ctk.CTkEntry(frame, width=400, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_isbn.insert(0, current["isbn"] if current["isbn"] != "-" else "")
        ent_isbn.pack(fill="x", pady=(0, 4))
        add_live_validation_with_hint(ent_isbn, validate_isbn, hint_isbn)

        ctk.CTkLabel(frame, text="Жанр", font=("Segoe UI", 15), text_color="#24292f").pack(anchor="w", pady=(3, 0))
        ent_genre = ctk.CTkComboBox(frame, values=self.genres_list, width=400, height=38, font=("Segoe UI", 14))
        ent_genre.set(current["genre"] or "")
        ent_genre.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(frame, text="Место на полке", font=("Segoe UI", 15), text_color="#24292f").pack(anchor="w", pady=(3, 0))
        ent_loc = ctk.CTkEntry(frame, width=400, height=38, font=("Segoe UI", 14), border_color="#d0d7de", fg_color="#f6f8fa")
        ent_loc.insert(0, current["location"] or "")
        ent_loc.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(frame, text="Статус", font=("Segoe UI", 15), text_color="#24292f").pack(anchor="w", pady=(2, 0))
        ent_status = ctk.CTkComboBox(frame, values=["В наличии", "Утрачена"], width=400, height=38, font=("Segoe UI", 14))
        ent_status.set(current["status"] if current["status"] in ("В наличии", "Утрачена") else "В наличии")
        ent_status.pack(fill="x", pady=(0, 4))

        error_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 14), text_color="#c62828")
        error_label.pack(pady=(2, 0))

        def save():
            title = ent_title.get().strip()
            author = ent_author.get().strip()
            from utils import validate_required, validate_year_str, validate_isbn
            genre = ent_genre.get() or None
            status = ent_status.get()
            if genre and genre not in self.genres_list:
                error_label.configure(text="Выберите жанр из списка")
                return
            if status not in ("В наличии", "Утрачена"):
                error_label.configure(text="Выберите статус из списка")
                return
            for err in [validate_required(title, "Название"), validate_required(author, "Автор"),
                        validate_year_str(ent_year.get()), validate_isbn(ent_isbn.get())]:
                if err:
                    error_label.configure(text=err)
                    return
            data = {
                "title": title, "author": author,
                "year": int(ent_year.get()) if ent_year.get().strip() else None,
                "isbn": ent_isbn.get().strip() or None,
                "genre": genre,
                "location": ent_loc.get().strip() or None,
                "status": status,
            }

            def do_patch():
                return self.client.patch(f"/books/{book_id}", data)

            def on_ok(_):
                dlg.after(50, dlg.destroy)
                self._show_status("Книга обновлена", "#2e7d32")
                self._load()

            def on_err(e):
                error_label.configure(text=str(e))

            run_async(dlg, do_patch, on_ok, on_err)

        ctk.CTkButton(card, text="Сохранить изменения", command=save,
                      width=200, height=42, font=("Segoe UI", 15, "bold"),
                      fg_color="#1565c0", hover_color="#0d47a1").pack(pady=4)

    def _delete_book(self):
        sel = self.tree.selection()
        if not sel:
            self._show_status("Выберите книгу", "#c62828")
            return
        book_id = self.tree.item(sel[0], "values")[0]

        from tkinter import messagebox
        if messagebox.askyesno("Подтверждение", f"Удалить книгу #{book_id}?"):
            def do_del():
                return self.client.delete(f"/books/{book_id}")

            def on_ok(_):
                self._show_status("Книга удалена", "#2e7d32")
                self._load()

            def on_err(e):
                self._show_status(f"Ошибка: {e}", "#c62828")

            run_async(self.parent, do_del, on_ok, on_err)
