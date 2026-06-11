# ============================================================
# Валидация входных данных
# ============================================================

import re
from datetime import date as _date


def validate_login(login: str | None) -> str | None:
    """Возвращает сообщение об ошибке или None если валидно."""
    login = (login or "").strip()
    if not login:
        return "Введите логин"
    if len(login) < 3:
        return "Логин: Логин должен содержать минимум 3 символа"
    if len(login) > 100:
        return "Логин: Логин может содержать максимум 100 символов"
    if not re.match(r'^[a-zA-Z0-9_-]+$', login):
        return "Логин может содержать только латиницу, цифры, _ и -"
    return None


def validate_password(password: str | None) -> str | None:
    password = password or ""
    if not password:
        return "Введите пароль"
    if len(password) < 8:
        return "Пароль: Пароль должен содержать минимум 8 символов"
    if len(password) > 255:
        return "Пароль: Пароль может содержать максимум 255 символов"
    return None


def validate_name(name: str | None, field_name: str = "Поле", required: bool = True) -> str | None:
    name = (name or "").strip()
    if required and not name:
        return f"Введите {field_name}"
    if name:
        if len(name) < 2:
            return f"{field_name}: минимум 2 символа"
        if not re.match(r'^[А-Яа-яЁё\-]+$', name):
            return f"{field_name} может содержать только русские буквы и дефис"
    return None


def validate_year(year_str: str | int | None) -> str | None:
    if year_str is None or year_str == "":
        return None
    try:
        year = int(year_str)
        current_year = _date.today().year
        if year < 1 or year > current_year:
            return f"Год издания: от 1 до {current_year}"
    except (ValueError, TypeError):
        return "Год должен быть числом"
    return None


def validate_isbn(isbn: str | None) -> str | None:
    isbn = (isbn or "").strip()
    if not isbn:
        return None
    isbn = isbn.strip()
    if not re.match(r'^\d{10,13}$', isbn):
        return "ISBN: ISBN от 10 до 13 цифр"
    return None


def validate_phone(phone: str | None) -> str | None:
    phone = (phone or "").strip()
    if not phone:
        return None
    if not re.match(r'^[0-9+\-\(\) ]+$', phone):
        return "Телефон может содержать только цифры, +, -, (, ), пробел"
    if len(phone) < 7:
        return "Телефон: Телефон должен содержать минимум 7 символов"
    if len(phone) > 20:
        return "Телефон: Телефон может содержать максимум 20 символов"
    return None


def validate_required(text: str | None, field_name: str = "Поле", max_len: int = 255) -> str | None:
    text = (text or "").strip()
    if not text:
        return f"Введите {field_name}"
    if len(text) > max_len:
        return f"{field_name}: максимум {max_len} символов"
    return None


def validate_positive_int(value, field_name: str = "Значение") -> str | None:
    try:
        v = int(value or "")
        if v <= 0:
            return f"{field_name} должно быть больше 0"
    except (ValueError, TypeError):
        return f"{field_name} должно быть числом"
    return None


def validate_date_str(date_str: str | None, field_name: str = "Дата") -> str | None:
    """Проверяет дату в формате ДД.ММ.ГГГГ."""
    date_str = (date_str or "").strip()
    if not date_str:
        return f"Введите {field_name}"
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, "%d.%m.%Y")
        d = dt.date()
        if d < _date.today():
            return f"{field_name} не может быть в прошлом"
        if d > _date(_date.today().year + 5, 12, 31):
            return f"{field_name}: максимум 5 лет вперёд"
    except ValueError:
        return f"{field_name}: неверный формат (ДД.ММ.ГГГГ)"
    return None


def validate_reader_card_id(card_id: str | None) -> str | None:
    card_id = (card_id or "").strip()
    if not card_id:
        return "Введите номер читательского билета"
    if not re.match(r'^\d{7}$', card_id):
        return "Номер билета — ровно 7 цифр"
    return None
