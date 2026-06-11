# ============================================================
# Главное окно приложения
# ============================================================

import customtkinter as ctk
from tkinter import ttk
from views.books_tab import BooksTab
from views.readers_tab import ReadersTab
from views.rentals_tab import RentalsTab
from views.admin_tab import AdminTab


class MainWindow(ctk.CTk):
    def __init__(self, client):
        super().__init__()
        self.client = client

        # Глобальный стиль для ttk Treeview
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 12), rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"))

        role_title = "Администратор" if client.is_admin() else "Библиотекарь"
        self.title(f"АИС Библиотека — {client.full_name}")
        self.minsize(1000, 620)
        self.configure(fg_color="#f0f2f5")
        self.after(0, lambda: self.state("zoomed"))

        # Верхняя панель
        header = ctk.CTkFrame(self, height=55, corner_radius=0, fg_color="#ffffff",
                              border_width=1, border_color="#d0d7de")
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="АИС Библиотека",
                     font=("Segoe UI", 19, "bold"), text_color="#1a1a2e").pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(header, text=f"{client.full_name}  |  {role_title}",
                     font=("Segoe UI", 14), text_color="#57606a").pack(side="left", padx=10, pady=10)

        ctk.CTkButton(header, text="Выход", width=85, height=34,
                      font=("Segoe UI", 15, "bold"),
                      fg_color="#c62828", hover_color="#b71c1c",
                      command=self._logout).pack(side="right", padx=20, pady=10)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Контент
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=15)

        # Вкладки
        self.tabview = ctk.CTkTabview(content, corner_radius=12,
                                      fg_color="white",
                                      border_width=1, border_color="#d0d7de",
                                      segmented_button_selected_color="#2e7d32",
                                      segmented_button_selected_hover_color="#1b5e20")
        self.tabview.pack(fill="both", expand=True)

        if client.role == "librarian":
            self.tab_books = self.tabview.add("Каталог")
            self.tab_readers = self.tabview.add("Читатели")
            self.tab_rentals = self.tabview.add("Аренда")

            BooksTab(self.tab_books, client)
            ReadersTab(self.tab_readers, client)
            RentalsTab(self.tab_rentals, client)
        elif client.is_admin():
            self.tab_admin = self.tabview.add("Администрирование")
            AdminTab(self.tab_admin, client)

    def _logout(self):
        self.withdraw()
        self.after(100, lambda: (self.destroy(), self._restart()))

    def _on_close(self):
        self.destroy()

    def _restart(self):
        from main import main
        main()
