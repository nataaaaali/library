# ============================================================
# Авторизация: bcrypt + JWT
# ============================================================

import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS


def hash_password(password: str) -> str:
    """Хеширует пароль."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Проверяет пароль против хеша."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user_login: str, role: str) -> str:
    """Создаёт JWT-токен."""
    payload = {
        "sub": user_login,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Раскодирует JWT-токен. Возвращает payload или бросает исключение."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
