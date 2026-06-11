# ============================================================
# Роутер управления пользователями (только admin)
# ============================================================

from fastapi import APIRouter, Request, HTTPException, Depends
from routers.auth import require_admin
import auth as auth_utils
import db_queries
from models import Administrator
import config

router = APIRouter()


def _admin_from_dict(user_dict: dict) -> Administrator:
    return Administrator(
        id=user_dict["id"], login=user_dict["login"],
        password_hash=user_dict["password_hash"],
        last_name=user_dict["last_name"], first_name=user_dict["first_name"],
        middle_name=user_dict.get("middle_name")
    )


@router.get("/users")
def list_users(current_user: dict = Depends(require_admin)):
    """Список всех пользователей."""
    users = db_queries.get_all_users()
    return users


@router.post("/users")
async def create_user(request: Request, current_user: dict = Depends(require_admin)):
    """Создание библиотекаря (admin only)."""
    data = await request.json()
    login = (data.get("login") or "").strip()
    password = data.get("password") or ""
    last_name = (data.get("last_name") or "").strip()
    first_name = (data.get("first_name") or "").strip()
    middle_name = (data.get("middle_name") or "").strip() or None

    from validators import validate_login, validate_password, validate_name
    for err in [validate_login(login), validate_password(password),
                validate_name(last_name, "Фамилия"), validate_name(first_name, "Имя"),
                validate_name(middle_name or "", "Отчество", required=False)]:
        if err:
            raise HTTPException(status_code=400, detail=err)

    if db_queries.get_user_by_login(login):
        raise HTTPException(status_code=400, detail="Логин уже занят")

    admin = _admin_from_dict(current_user)
    password_hash = auth_utils.hash_password(password)
    librarian = admin.add_librarian(login, password_hash, last_name, first_name, middle_name)
    return librarian.to_dict()


@router.delete("/users/{user_id}")
def remove_user(user_id: int, current_user: dict = Depends(require_admin)):
    """Удаление библиотекаря (admin only)."""
    user_to_delete = db_queries.get_user_by_id(user_id)
    name = f"{user_to_delete.get('last_name', '')} {user_to_delete.get('first_name', '')}".strip() if user_to_delete else f"ID {user_id}"
    admin = _admin_from_dict(current_user)
    db_queries.delete_user(user_id)
    db_queries.log_event(current_user["id"], "delete_librarian", f"{name} (ID {user_id})")
    return {"message": "Пользователь удалён"}


@router.post("/maintenance/toggle")
def toggle_maintenance(current_user: dict = Depends(require_admin)):
    """Переключение режима технического обслуживания."""
    config.MAINTENANCE_MODE = not config.MAINTENANCE_MODE
    config.save_maintenance_state(config.MAINTENANCE_MODE)
    return {"maintenance": config.MAINTENANCE_MODE}
