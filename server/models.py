import db_queries
from datetime import date, timedelta


class User:
    def __init__(self, id=None, login=None, password_hash=None,
                 last_name=None, first_name=None, middle_name=None, role=None):
        self.id = id
        self.login = login
        self.password_hash = password_hash
        self.last_name = last_name
        self.first_name = first_name
        self.middle_name = middle_name
        self.role = role

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(p for p in parts if p)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "login": self.login,
            "full_name": self.full_name,
            "role": self.role,
        }


class Administrator(User):
    def __init__(self, id=None, login=None, password_hash=None,
                 last_name=None, first_name=None, middle_name=None):
        super().__init__(id, login, password_hash, last_name, first_name, middle_name, role="admin")

    def add_librarian(self, login: str, password_hash: str,
                      last_name: str, first_name: str, middle_name: str = None) -> "Librarian":
        """Создаёт библиотекаря в БД."""
        user_data = {
            "login": login,
            "password_hash": password_hash,
            "last_name": last_name,
            "first_name": first_name,
            "middle_name": middle_name,
            "role": "librarian",
        }
        user_id = db_queries.save_user(user_data)
        db_queries.log_event(self.id, "add_librarian", f"{last_name} {first_name} (логин: {login})")
        return Librarian(
            id=user_id, login=login, password_hash=password_hash,
            last_name=last_name, first_name=first_name, middle_name=middle_name
        )

    def delete_librarian(self, user_id: int):
        """Удаляет библиотекаря из БД."""
        db_queries.delete_user(user_id)
        user = db_queries.get_user_by_id(user_id)
        name = f"{user.get('last_name', '')} {user.get('first_name', '')}".strip() if user else f"ID {user_id}"
        db_queries.log_event(self.id, "delete_librarian", f"{name} (ID {user_id})")


class Librarian(User):
    def __init__(self, id=None, login=None, password_hash=None,
                 last_name=None, first_name=None, middle_name=None):
        super().__init__(id, login, password_hash, last_name, first_name, middle_name, role="librarian")

    def process_rental(self, book_id: int, reader_card_id: str,
                       issue_date: date, duration_days: int) -> "Rental":
        """Оформляет выдачу книги."""
        book = db_queries.get_book_by_id(book_id)
        if book and book.get("status") == "Выдана":
            raise ValueError("Книга уже в аренде")
        if db_queries.get_active_rental_for_book(book_id):
            raise ValueError("Книга уже в аренде")
        due_date = issue_date + timedelta(days=duration_days)
        rental_data = {
            "book_id": book_id,
            "reader_card_id": reader_card_id,
            "librarian_id": self.id,
            "issue_date": issue_date,
            "due_date": due_date,
        }
        rental_id = db_queries.create_rental(rental_data)
        db_queries.update_book_status(book_id, "Выдана")
        book = db_queries.get_book_by_id(book_id)
        reader = db_queries.get_reader_card(reader_card_id)
        book_title = book.get("title", f"ID {book_id}") if book else f"ID {book_id}"
        reader_name = f"{reader.get('last_name', '')} {reader.get('first_name', '')}".strip() if reader else reader_card_id
        db_queries.log_event(self.id, "process_rental", f"'{book_title}' → {reader_name} (билет {reader_card_id})")
        return Rental(
            id=rental_id, book_id=book_id, reader_card_id=reader_card_id,
            librarian_id=self.id, issue_date=issue_date, due_date=due_date
        )

    def extend_rental(self, rental_id: int, new_due_date: date) -> "ExtensionRecord":
        """Продляет срок аренды."""
        rental = db_queries.get_rental_by_id(rental_id)
        if rental.get("actual_return_date"):
            raise ValueError("Аренда уже закрыта, продление невозможно")
        ext_data = {
            "rental_id": rental_id,
            "extension_date": date.today(),
            "new_due_date": new_due_date,
            "librarian_id": self.id,
        }
        db_queries.create_extension(ext_data)
        db_queries.update_rental_due_date(rental_id, new_due_date)
        rental = db_queries.get_rental_by_id(rental_id)
        book_title = rental.get("book_title", f"аренда {rental_id}") if rental else f"аренда {rental_id}"
        db_queries.log_event(self.id, "extend_rental", f"Продление '{book_title}' до {new_due_date}")
        return ExtensionRecord(
            rental_id=rental_id, extension_date=date.today(),
            new_due_date=new_due_date, librarian_id=self.id
        )

    def process_return(self, rental_id: int, actual_return_date: date) -> float:
        """Оформляет возврат, считает штраф. Возвращает сумму штрафа."""
        rental_dict = db_queries.get_rental_by_id(rental_id)
        if rental_dict.get("actual_return_date"):
            raise ValueError("Книга уже возвращена")
        due_date = rental_dict["due_date"]
        fine = 0.0
        is_overdue = False
        if actual_return_date > due_date:
            days = (actual_return_date - due_date).days
            fine = days * 10.0
            is_overdue = True
        db_queries.close_rental(rental_id, actual_return_date, fine, is_overdue)
        db_queries.update_book_status(rental_dict["book_id"], "В наличии")
        rental = db_queries.get_rental_by_id(rental_id)
        book_title = rental.get("book_title", f"аренда {rental_id}") if rental else f"аренда {rental_id}"
        db_queries.log_event(self.id, "process_return", f"'{book_title}' возвращена, штраф {fine:.2f}")
        return fine

    def register_reader(self, last_name: str, first_name: str,
                        middle_name: str = None, phone: str = None,
                        expiration_date: date = None) -> "ReaderCard":
        """Регистрирует нового читателя."""
        if expiration_date is None:
            expiration_date = date.today() + timedelta(days=365)
        card_id = db_queries.generate_reader_card_id()
        reader_data = {
            "id": card_id,
            "last_name": last_name,
            "first_name": first_name,
            "middle_name": middle_name,
            "phone": phone,
            "expiration_date": expiration_date,
        }
        db_queries.save_reader_card(reader_data)
        db_queries.log_event(self.id, "register_reader", f"{last_name} {first_name} (билет {card_id})")
        return ReaderCard(
            card_id, last_name, first_name, middle_name, phone,
            issue_date=date.today(), expiration_date=expiration_date
        )

    def update_reader_info(self, card_id: str, phone: str,
                           last_name: str = None, first_name: str = None,
                           middle_name: str = None) -> dict:
        """Обновляет данные читателя в БД. Возвращает обновлённый словарь."""
        updates = {"phone": phone}
        if last_name:
            updates["last_name"] = last_name
        if first_name:
            updates["first_name"] = first_name
        if middle_name:
            updates["middle_name"] = middle_name
        db_queries.update_reader_card(card_id, updates)
        return db_queries.get_reader_card(card_id)

    def renew_reader_card(self, card_id: str, new_expiration_date: date):
        """Продлевает срок действия билета."""
        db_queries.update_reader_card(card_id, {"expiration_date": new_expiration_date})
        reader = db_queries.get_reader_card(card_id)
        name = f"{reader.get('last_name', '')} {reader.get('first_name', '')}".strip() if reader else card_id
        db_queries.log_event(self.id, "renew_card", f"{name} (билет {card_id}) → {new_expiration_date}")

    def update_book_status(self, book_id: int, status: str):
        """Меняет статус книги."""
        db_queries.update_book_status(book_id, status)

    def get_catalog(self, filters: dict = None) -> list["Book"]:
        """Загружает каталог из БД."""
        catalog = Catalog()
        books_data = db_queries.get_all_books()
        catalog.books = [Book(**b) for b in books_data]
        return catalog.search(filters) if filters else catalog.get_all()

    def add_book(self, title: str, author: str, year: int = None,
                 isbn: str = None, genre: str = None, location: str = None) -> "Book":
        """Добавляет книгу в БД."""
        book_data = {
            "title": title,
            "author": author,
            "year": year,
            "isbn": isbn,
            "genre": genre,
            "location": location,
            "status": "В наличии",
        }
        book_id = db_queries.save_book(book_data)
        db_queries.log_event(self.id, "add_book", f"'{title}'")
        return Book(
            id=book_id, title=title, author=author, year=year,
            isbn=isbn, genre=genre, location=location, status="В наличии"
        )

    def delete_book(self, book_id: int):
        """Удаляет книгу из БД."""
        db_queries.delete_book(book_id)
        book = db_queries.get_book_by_id(book_id)
        title = book.get("title", f"ID {book_id}") if book else f"ID {book_id}"
        db_queries.log_event(self.id, "delete_book", f"'{title}'")


class ReaderCard:
    def __init__(self, card_id: str, last_name: str, first_name: str,
                 middle_name: str = None, phone: str = None,
                 issue_date: date = None, expiration_date: date = None):
        self.id = card_id
        self.last_name = last_name
        self.first_name = first_name
        self.middle_name = middle_name
        self.phone = phone
        self.issue_date = issue_date
        self.expiration_date = expiration_date

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(p for p in parts if p)

    @property
    def is_expired(self) -> bool:
        if self.expiration_date:
            return date.today() > self.expiration_date
        return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "phone": self.phone,
            "issue_date": str(self.issue_date) if self.issue_date else None,
            "expiration_date": str(self.expiration_date) if self.expiration_date else None,
            "is_expired": self.is_expired,
        }


class Book:
    def __init__(self, id=None, title=None, author=None, year=None,
                 isbn=None, genre=None, location=None, status=None):
        self.id = id
        self.title = title
        self.author = author
        self.year = year
        self.isbn = isbn
        self.genre = genre
        self.location = location
        self.status = status

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "isbn": self.isbn,
            "genre": self.genre,
            "location": self.location,
            "status": self.status,
        }


class Catalog:
    def __init__(self):
        self.books = []

    def search_by_author(self, author: str) -> list[Book]:
        return [b for b in self.books if author.lower() in b.author.lower()]

    def search_by_title(self, title: str) -> list[Book]:
        return [b for b in self.books if title.lower() in b.title.lower()]

    def search_by_genre(self, genre: str) -> list[Book]:
        return [b for b in self.books if b.genre and genre.lower() in b.genre.lower()]

    def search_by_status(self, status: str) -> list[Book]:
        return [b for b in self.books if b.status == status]

    def search_by_year(self, year: int) -> list[Book]:
        return [b for b in self.books if b.year == year]

    def get_all(self) -> list[Book]:
        return self.books

    def search(self, filters: dict) -> list[Book]:
        """filters: {author, title, genre, status, year}"""
        result = self.books[:]
        if filters.get("author"):
            result = [b for b in result if filters["author"].lower() in b.author.lower()]
        if filters.get("title"):
            result = [b for b in result if filters["title"].lower() in b.title.lower()]
        if filters.get("genre"):
            result = [b for b in result if b.genre and filters["genre"].lower() in b.genre.lower()]
        if filters.get("status"):
            result = [b for b in result if b.status == filters["status"]]
        if filters.get("year"):
            result = [b for b in result if b.year == int(filters["year"])]
        return result


class Rental:
    def __init__(self, id=None, book_id=None, reader_card_id=None, librarian_id=None,
                 issue_date=None, due_date=None, actual_return_date=None,
                 is_overdue=False, fine_amount=0.0):
        self.id = id
        self.book_id = book_id
        self.reader_card_id = reader_card_id
        self.librarian_id = librarian_id
        self.issue_date = issue_date
        self.due_date = due_date
        self.actual_return_date = actual_return_date
        self.is_overdue = is_overdue
        self.fine_amount = fine_amount
        self.extension_history = []

    def calculate_fine(self, return_date: date) -> float:
        if return_date > self.due_date:
            days = (return_date - self.due_date).days
            return days * 10.0
        return 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "book_id": self.book_id,
            "reader_card_id": self.reader_card_id,
            "librarian_id": self.librarian_id,
            "issue_date": str(self.issue_date) if self.issue_date else None,
            "due_date": str(self.due_date) if self.due_date else None,
            "actual_return_date": str(self.actual_return_date) if self.actual_return_date else None,
            "is_overdue": self.is_overdue,
            "fine_amount": self.fine_amount,
        }


class ExtensionRecord:
    def __init__(self, id=None, rental_id=None, extension_date=None,
                 new_due_date=None, librarian_id=None):
        self.id = id
        self.rental_id = rental_id
        self.extension_date = extension_date
        self.new_due_date = new_due_date
        self.librarian_id = librarian_id

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rental_id": self.rental_id,
            "extension_date": str(self.extension_date) if self.extension_date else None,
            "new_due_date": str(self.new_due_date) if self.new_due_date else None,
            "librarian_id": self.librarian_id,
        }


class Logger:
    """Пишет действия пользователей в audit_logs (через db_queries.py)."""

    @staticmethod
    def log_event(user_id: int | None, action: str, details: str = ""):
        db_queries.log_event(user_id, action, details)
