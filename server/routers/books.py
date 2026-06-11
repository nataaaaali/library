# ============================================================
# Роутер каталога книг (библиотекарь)
# ============================================================

from fastapi import APIRouter, Request, HTTPException, Depends
from routers.auth import require_librarian
import db_queries
from models import Librarian, Book

router = APIRouter()


def _librarian_from_dict(user_dict: dict) -> Librarian:
    return Librarian(
        id=user_dict["id"], login=user_dict["login"],
        password_hash=user_dict["password_hash"],
        last_name=user_dict["last_name"], first_name=user_dict["first_name"],
        middle_name=user_dict.get("middle_name")
    )


@router.get("/genres")
def list_genres(current_user: dict = Depends(require_librarian)):
    """Список жанров."""
    return db_queries.get_all_genres()


@router.get("/books")
def list_books(current_user: dict = Depends(require_librarian)):
    """Список всех книг."""
    lib = _librarian_from_dict(current_user)
    books = lib.get_catalog()
    return [b.to_dict() for b in books]


@router.post("/books/search")
async def search_books(request: Request, current_user: dict = Depends(require_librarian)):
    """Поиск книг по фильтрам."""
    data = await request.json() or {}
    lib = _librarian_from_dict(current_user)
    books = lib.get_catalog(filters=data)
    return [b.to_dict() for b in books]


@router.post("/books")
async def create_book(request: Request, current_user: dict = Depends(require_librarian)):
    """Добавление книги."""
    data = await request.json()
    title = (data.get("title") or "").strip()
    author = (data.get("author") or "").strip()
    from validators import validate_required, validate_year, validate_isbn
    for err in [validate_required(title, "Название"), validate_required(author, "Автор"),
                validate_year(data.get("year")), validate_isbn(data.get("isbn"))]:
        if err:
            raise HTTPException(status_code=400, detail=err)

    lib = _librarian_from_dict(current_user)
    book = lib.add_book(
        title=title,
        author=author,
        year=data.get("year"),
        isbn=data.get("isbn"),
        genre=data.get("genre"),
        location=data.get("location"),
    )
    return book.to_dict()


@router.patch("/books/{book_id}")
async def update_book(book_id: int, request: Request, current_user: dict = Depends(require_librarian)):
    """Обновление книги (включая статус)."""
    data = await request.json()
    if not data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    old = db_queries.get_book_by_id(book_id)
    if not old:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    if "status" in data:
        lib = _librarian_from_dict(current_user)
        lib.update_book_status(book_id, data["status"])

    # Обновление остальных полей
    book_data = {
        "title": data.get("title"),
        "author": data.get("author"),
        "year": data.get("year"),
        "isbn": data.get("isbn"),
        "genre": data.get("genre"),
        "location": data.get("location"),
        "status": data.get("status", "В наличии"),
    }
    # Убираем None, чтобы не затереть существующие значения
    book_data = {k: v for k, v in book_data.items() if v is not None}
    db_queries.update_book(book_id, book_data)

    updated = db_queries.get_book_by_id(book_id)

    # Формируем детали изменений для лога
    changes = []
    field_names = {
        "title": "Название",
        "author": "Автор",
        "year": "Год",
        "isbn": "ISBN",
        "genre": "Жанр",
        "location": "Место",
        "status": "Статус",
    }
    for key, name in field_names.items():
        old_val = old.get(key)
        new_val = updated.get(key)
        old_str = str(old_val) if old_val is not None else ""
        new_str = str(new_val) if new_val is not None else ""
        if old_str != new_str:
            changes.append(f"{name}: '{old_str}' → '{new_str}'")

    if changes:
        action = "update_status" if len(changes) == 1 and changes[0].startswith("Статус:") else "update_book"
        db_queries.log_event(
            current_user["id"],
            action,
            f"'{old.get('title', '')}' — {', '.join(changes)}"
        )

    return updated


@router.delete("/books/{book_id}")
def remove_book(book_id: int, current_user: dict = Depends(require_librarian)):
    """Удаление книги."""
    if db_queries.count_rentals_for_book(book_id) > 0:
        raise HTTPException(status_code=400, detail="Нельзя удалить книгу с историей аренд")
    lib = _librarian_from_dict(current_user)
    lib.delete_book(book_id)
    return {"message": "Книга удалена"}
