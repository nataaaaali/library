# ============================================================
# Роутер читателей (библиотекарь)
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


@router.get("/readers")
def list_readers(current_user: dict = Depends(require_librarian)):
    """Список всех читательских билетов."""
    return db_queries.get_all_reader_cards()


@router.get("/readers/{card_id}")
def get_reader(card_id: str, current_user: dict = Depends(require_librarian)):
    """Информация о читателе."""
    reader = db_queries.get_reader_card(card_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Билет не найден")
    return reader


@router.post("/readers")
async def create_reader(request: Request, current_user: dict = Depends(require_librarian)):
    """Регистрация нового читателя."""
    data = await request.json()
    last_name = (data.get("last_name") or "").strip()
    first_name = (data.get("first_name") or "").strip()
    from validators import validate_name, validate_phone
    for err in [validate_name(last_name, "Фамилия"), validate_name(first_name, "Имя"),
                validate_name(data.get("middle_name"), "Отчество", required=False),
                validate_phone(data.get("phone"))]:
        if err:
            raise HTTPException(status_code=400, detail=err)

    expiration = data.get("expiration_date")
    if expiration:
        from validators import validate_date_str
        err = validate_date_str(expiration, "Действует до")
        if err:
            raise HTTPException(status_code=400, detail=err)
        expiration = datetime.strptime(expiration.strip(), "%d.%m.%Y").date()
    else:
        expiration = None

    lib = _librarian_from_dict(current_user)
    card = lib.register_reader(
        last_name=last_name,
        first_name=first_name,
        middle_name=(data.get("middle_name") or "").strip() or None,
        phone=(data.get("phone") or "").strip() or None,
        expiration_date=expiration,
    )
    return card.to_dict()


@router.patch("/readers/{card_id}")
async def update_reader(card_id: str, request: Request, current_user: dict = Depends(require_librarian)):
    """Обновление данных читателя."""
    data = await request.json()
    phone = (data.get("phone") or "").strip() or None

    from validators import validate_name, validate_phone
    ln = (data.get("last_name") or "").strip() or None
    fn = (data.get("first_name") or "").strip() or None
    mn = (data.get("middle_name") or "").strip() or None
    for err in [validate_name(ln or "", "Фамилия", required=False),
                validate_name(fn or "", "Имя", required=False),
                validate_name(mn or "", "Отчество", required=False),
                validate_phone(phone or "")]:
        if err:
            raise HTTPException(status_code=400, detail=err)

    old = db_queries.get_reader_card(card_id)
    if not old:
        raise HTTPException(status_code=404, detail="Читатель не найден")

    lib = _librarian_from_dict(current_user)
    result = lib.update_reader_info(
        card_id=card_id,
        phone=phone,
        last_name=ln,
        first_name=fn,
        middle_name=mn,
    )

    # Формируем детали изменений для лога
    changes = []
    field_names = {
        "last_name": "Фамилия",
        "first_name": "Имя",
        "middle_name": "Отчество",
        "phone": "Телефон",
    }
    for key, name in field_names.items():
        old_val = old.get(key)
        new_val = result.get(key)
        old_str = str(old_val) if old_val is not None else ""
        new_str = str(new_val) if new_val is not None else ""
        if old_str != new_str:
            changes.append(f"{name}: '{old_str}' → '{new_str}'")

    if changes:
        old_name = f"{old.get('last_name', '')} {old.get('first_name', '')}".strip()
        db_queries.log_event(
            current_user["id"],
            "update_reader",
            f"{old_name} (билет {card_id}) — {', '.join(changes)}"
        )

    return result


@router.post("/readers/{card_id}/renew")
async def renew_card(card_id: str, request: Request, current_user: dict = Depends(require_librarian)):
    """Продление срока действия билета."""
    data = await request.json()
    new_date_str = data.get("expiration_date")
    if not new_date_str:
        raise HTTPException(status_code=400, detail="Укажите новую дату окончания")

    from validators import validate_date_str
    err = validate_date_str(new_date_str, "Новая дата окончания")
    if err:
        raise HTTPException(status_code=400, detail=err)
    new_date = datetime.strptime(new_date_str.strip(), "%d.%m.%Y").date()
    lib = _librarian_from_dict(current_user)
    lib.renew_reader_card(card_id, new_date)
    return db_queries.get_reader_card(card_id)
