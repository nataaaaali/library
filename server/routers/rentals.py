# ============================================================
# Роутер аренды (библиотекарь)
# ============================================================

from fastapi import APIRouter, Request, HTTPException, Depends
from routers.auth import require_librarian
import db_queries
from models import Librarian
from datetime import date, datetime

router = APIRouter()


def _librarian_from_dict(user_dict: dict) -> Librarian:
    return Librarian(
        id=user_dict["id"], login=user_dict["login"],
        password_hash=user_dict["password_hash"],
        last_name=user_dict["last_name"], first_name=user_dict["first_name"],
        middle_name=user_dict.get("middle_name")
    )


@router.get("/rentals")
def list_rentals(current_user: dict = Depends(require_librarian)):
    """Список всех аренд."""
    return db_queries.get_all_rentals()


@router.get("/rentals/active")
def active_rentals(current_user: dict = Depends(require_librarian)):
    """Только активные аренды (не возвращённые)."""
    return db_queries.get_all_rentals(active_only=True)


@router.post("/rentals")
async def create_rental(request: Request, current_user: dict = Depends(require_librarian)):
    """Оформление выдачи книги."""
    data = await request.json()
    book_id = data.get("book_id")
    reader_card_id = data.get("reader_card_id")
    duration = data.get("duration_days", 14)

    from validators import validate_positive_int, validate_reader_card_id
    for err in [validate_positive_int(book_id, "ID книги"),
                validate_reader_card_id(reader_card_id),
                validate_positive_int(duration, "Срок аренды")]:
        if err:
            raise HTTPException(status_code=400, detail=err)

    # Проверяем, не в аренде ли книга
    book = db_queries.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    if book.get("status") == "Выдана":
        raise HTTPException(status_code=400, detail="Книга уже в аренде")
    active_rental = db_queries.get_active_rental_for_book(book_id)
    if active_rental:
        raise HTTPException(status_code=400, detail="Книга уже в аренде")

    lib = _librarian_from_dict(current_user)
    rental = lib.process_rental(
        book_id=int(book_id),
        reader_card_id=reader_card_id,
        issue_date=date.today(),
        duration_days=int(duration),
    )
    return rental.to_dict()


@router.post("/rentals/{rental_id}/return")
async def return_book(rental_id: int, request: Request, current_user: dict = Depends(require_librarian)):
    """Оформление возврата."""
    data = await request.json() or {}
    return_date_str = data.get("return_date")
    if return_date_str:
        try:
            return_date = datetime.strptime(return_date_str.strip(), "%d.%m.%Y").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Дата возврата: неверный формат (ДД.ММ.ГГГГ)")
    else:
        return_date = date.today()

    lib = _librarian_from_dict(current_user)
    try:
        fine = lib.process_return(rental_id, return_date)
        return {"message": "Книга возвращена", "fine": fine}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rentals/{rental_id}/extend")
async def extend_rental(rental_id: int, request: Request, current_user: dict = Depends(require_librarian)):
    """Продление срока аренды."""
    data = await request.json()
    new_due_str = data.get("new_due_date")
    if not new_due_str:
        raise HTTPException(status_code=400, detail="Укажите новую дату возврата")

    from validators import validate_date_str
    err = validate_date_str(new_due_str, "Новая дата возврата")
    if err:
        raise HTTPException(status_code=400, detail=err)
    try:
        new_due = datetime.strptime(new_due_str.strip(), "%d.%m.%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Новая дата возврата: неверный формат (ДД.ММ.ГГГГ)")
    lib = _librarian_from_dict(current_user)
    try:
        ext = lib.extend_rental(rental_id, new_due)
        return ext.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
