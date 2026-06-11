# ============================================================
# Роутер авторизации
# ============================================================

from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timezone, timedelta
import auth as auth_utils
import db_queries
import config
from config import MAX_LOGIN_ATTEMPTS, LOCKOUT_MINUTES, ATTEMPT_WINDOW_MINUTES
from models import Administrator, Librarian

router = APIRouter()

# In-memory хранилище попыток входа: {(ip, login): {"count": int, "first_attempt_at": datetime|None, "locked_until": datetime|None}}
_login_attempts = {}


def _get_user_model(user_dict: dict):
    """Создаёт объект Administrator или Librarian из словаря."""
    if user_dict["role_name"] == "admin":
        return Administrator(
            id=user_dict["id"], login=user_dict["login"],
            password_hash=user_dict["password_hash"],
            last_name=user_dict["last_name"], first_name=user_dict["first_name"],
            middle_name=user_dict.get("middle_name")
        )
    return Librarian(
        id=user_dict["id"], login=user_dict["login"],
        password_hash=user_dict["password_hash"],
        last_name=user_dict["last_name"], first_name=user_dict["first_name"],
        middle_name=user_dict.get("middle_name")
    )


def get_current_user(token: str = Header(None, alias="Authorization")):
    """Dependency: проверяет JWT и возвращает словарь пользователя."""
    if not token:
        raise HTTPException(status_code=401, detail="Токен не предоставлен")
    if token.startswith("Bearer "):
        token = token[7:]
    try:
        payload = auth_utils.decode_token(token)
        user = db_queries.get_user_by_login(payload["sub"])
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Недействительный токен")


def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency: только для администраторов."""
    if current_user["role_name"] != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён: требуется роль администратора")
    return current_user


def require_librarian(current_user: dict = Depends(get_current_user)):
    """Dependency: только для библиотекарей."""
    if current_user["role_name"] != "librarian":
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return current_user


def _parse_log_date(date_str: str) -> str | None:
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str.strip(), "%d.%m.%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


@router.get("/logs")
def get_logs(limit: int = 50, offset: int = 0, action: str = None,
             user_query: str = None, date_from: str = None, date_to: str = None,
             current_user: dict = Depends(require_admin)):
    """Логи аудита с пагинацией и фильтрами (admin only)."""
    parsed_from = _parse_log_date(date_from) if date_from else None
    parsed_to = _parse_log_date(date_to) if date_to else None
    logs = db_queries.get_audit_logs(
        limit=limit, offset=offset, action=action,
        user_query=user_query, date_from=parsed_from, date_to=parsed_to
    )
    total = db_queries.count_audit_logs(
        action=action, user_query=user_query,
        date_from=parsed_from, date_to=parsed_to
    )
    return {"logs": logs, "total": total}


@router.post("/login")
async def login(request: Request):
    """Авторизация. Блокировка после 5 неудачных попыток с одного IP (in-memory)."""
    data = await request.json()
    login_str = (data.get("login") or "").strip()
    password = data.get("password") or ""
    client_ip = request.client.host if request.client else "unknown"
    attempt_key = (client_ip, login_str)

    from validators import validate_login, validate_password
    login_err = validate_login(login_str)
    if login_err:
        raise HTTPException(status_code=400, detail=login_err)
    pass_err = validate_password(password)
    if pass_err:
        raise HTTPException(status_code=400, detail=pass_err)

    user = db_queries.get_user_by_login(login_str)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    now = datetime.now(timezone.utc)
    record = _login_attempts.get(attempt_key, {"count": 0, "first_attempt_at": None, "locked_until": None})

    # Проверка блокировки по IP + логин
    locked_until = record.get("locked_until")
    if locked_until:
        if locked_until > now:
            remaining = locked_until - now
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            detail = f"Аккаунт заблокирован. Попробуйте через {minutes} мин {seconds} сек."
            locked_str = locked_until.astimezone().strftime("%d.%m.%Y %H:%M:%S")
            db_queries.log_event(user["id"], "login_failed", f"Попытка входа в заблокированный аккаунт с IP {client_ip} (до {locked_str})")
            raise HTTPException(status_code=403, detail=detail)
        else:
            record = {"count": 0, "first_attempt_at": None, "locked_until": None}
            _login_attempts[attempt_key] = record

    # Сброс счётчика, если с момента первой попытки прошло больше окна
    first_attempt = record.get("first_attempt_at")
    if first_attempt and (now - first_attempt) > timedelta(minutes=ATTEMPT_WINDOW_MINUTES):
        record = {"count": 0, "first_attempt_at": None, "locked_until": None}
        _login_attempts[attempt_key] = record

    # Проверка пароля
    if not auth_utils.verify_password(password, user["password_hash"]):
        if record["count"] == 0:
            record["first_attempt_at"] = now
        record["count"] += 1
        if record["count"] >= MAX_LOGIN_ATTEMPTS:
            record["locked_until"] = now + timedelta(minutes=LOCKOUT_MINUTES)
            locked_str = record["locked_until"].astimezone().strftime("%d.%m.%Y %H:%M:%S")
            db_queries.log_event(user["id"], "account_locked", f"Аккаунт заблокирован с IP {client_ip} до {locked_str} после {MAX_LOGIN_ATTEMPTS} неудачных попыток")
        else:
            db_queries.log_event(user["id"], "login_failed", f"Неверный пароль с IP {client_ip} (попытка {record['count']}/{MAX_LOGIN_ATTEMPTS})")
        _login_attempts[attempt_key] = record
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    # Проверка режима технического обслуживания
    if config.MAINTENANCE_MODE and user["role_name"] != "admin":
        raise HTTPException(status_code=403, detail="Система на техническом обслуживании. Вход разрешён только администраторам.")

    # Успешный вход — сброс счётчика для этой пары IP+логин
    if attempt_key in _login_attempts:
        del _login_attempts[attempt_key]
    db_queries.log_event(user["id"], "login", "Успешный вход")

    token = auth_utils.create_token(user["login"], user["role_name"])
    return {
        "token": token,
        "role": user["role_name"],
        "full_name": f"{user['last_name']} {user['first_name']} {user.get('middle_name') or ''}".strip(),
    }
