# ============================================================
# Конфигурация сервера АИС "Библиотека"
# ============================================================

import os
import json

from dotenv import load_dotenv

# Загружаем переменные из .env (лежит в корне проекта, рядом с server/)
# override=True — .env всегда перекрывает системные env-переменные
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=True)

# Пути (относительно папки server/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

# PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "library_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "12345")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "library-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 8

# HTTPS (self-signed)
SSL_CERT_PATH = os.path.join(ROOT_DIR, "server.crt")
SSL_KEY_PATH = os.path.join(ROOT_DIR, "server.key")

# Безопасность
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
ATTEMPT_WINDOW_MINUTES = 15

# Настройки сервера
HOST = "0.0.0.0"
PORT = 8000

# Режим технического обслуживания (сохраняется в файл)
_MAINTENANCE_FILE = os.path.join(ROOT_DIR, "maintenance_state.json")


def _load_maintenance():
    if os.path.exists(_MAINTENANCE_FILE):
        try:
            with open(_MAINTENANCE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return bool(data.get("maintenance", False))
        except Exception:
            pass
    return os.getenv("MAINTENANCE_MODE", "false").lower() == "true"


def save_maintenance_state(value: bool):
    try:
        with open(_MAINTENANCE_FILE, "w", encoding="utf-8") as f:
            json.dump({"maintenance": value}, f)
    except Exception:
        pass


MAINTENANCE_MODE = _load_maintenance()
