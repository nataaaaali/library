# ============================================================
# Утилиты клиента
# ============================================================

import threading
import re
from datetime import datetime


# ------------------------------------------------------------
# Пропорциональные колонки Treeview
# ------------------------------------------------------------
def bind_tree_columns(tree, ratios: dict):
    """Привязывает ширины колонок Treeview к пропорциям ratios {col: fraction}.
    Биндит <Configure> на родителя tree, чтобы избежать рекурсии."""
    def _update(event=None):
        w = tree.winfo_width()
        if w < 50:
            return
        for col, ratio in ratios.items():
            tree.column(col, width=int(w * ratio))
    parent = tree.master
    parent.bind("<Configure>", _update, add="+")
    tree.after(200, _update)


# ------------------------------------------------------------
# Центрирование и ограничение размера диалога
# ------------------------------------------------------------
def center_dialog(dialog, width: int = None, height: int = None, resizable: bool = True, max_ratio: float = 0.95):
    """Устанавливает geometry диалога по содержимому (или заданному размеру), ограничивая долей экрана, и центрирует.
    Если clamped-размер меньше запрошенного, диалог делается resizable."""
    dialog.update_idletasks()
    screen_w = dialog.winfo_screenwidth()
    screen_h = dialog.winfo_screenheight()
    max_w = int(screen_w * max_ratio)
    max_h = int(screen_h * max_ratio)
    req_w = dialog.winfo_reqwidth()
    req_h = dialog.winfo_reqheight()
    # fallback если ctk ещё не отрисовал
    if req_w < 100:
        req_w = width or 400
    if req_h < 100:
        req_h = height or 400
    use_w = min(width or req_w, max_w)
    use_h = min(height or req_h, max_h)
    # Если clamped меньше req — нужно дать пользователю возможность растянуть
    if use_h < req_h or use_w < req_w:
        dialog.resizable(True, True)
    else:
        dialog.resizable(resizable, resizable)
    x = max(0, (screen_w - use_w) // 2)
    y = max(0, (screen_h - use_h) // 2)
    dialog.geometry(f"{use_w}x{use_h}+{x}+{y}")
    dialog.minsize(300, 200)


# ------------------------------------------------------------
# Перевод ролей
# ------------------------------------------------------------
def translate_role(role: str) -> str:
    mapping = {
        "admin": "Администратор",
        "librarian": "Библиотекарь",
    }
    return mapping.get(role, role)


# ------------------------------------------------------------
# Перевод действий в логах
# ------------------------------------------------------------
ACTION_CHOICES = [
    ("", "Все"),
    ("login", "Вход в систему"),
    ("login_failed", "Неудачная попытка входа"),
    ("account_locked", "Блокировка аккаунта"),
    ("add_librarian", "Создание библиотекаря"),
    ("delete_librarian", "Удаление библиотекаря"),
    ("add_book", "Добавление книги"),
    ("delete_book", "Удаление книги"),
    ("update_status", "Изменение статуса книги"),
    ("update_book", "Редактирование книги"),
    ("process_rental", "Выдача книги"),
    ("extend_rental", "Продление аренды"),
    ("process_return", "Возврат книги"),
    ("register_reader", "Регистрация читателя"),
    ("update_reader", "Обновление данных читателя"),
    ("renew_card", "Продление билета"),
]


def translate_action(action: str) -> str:
    mapping = {k: v for k, v in ACTION_CHOICES if k}
    return mapping.get(action, action)


# ------------------------------------------------------------
# Форматирование даты/времени (без миллисекунд)
# ------------------------------------------------------------
def format_datetime(dt_str: str) -> str:
    """Преобразует ISO-строку в локальное время 'ДД.ММ.ГГГГ ЧЧ:ММ:СС'."""
    if not dt_str:
        return ""
    try:
        from datetime import timezone
        if isinstance(dt_str, datetime):
            dt = dt_str
        else:
            dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone()
        else:
            dt = dt.replace(tzinfo=timezone.utc).astimezone()
        return dt.strftime("%d.%m.%Y %H:%M:%S")
    except Exception:
        return str(dt_str)[:19].replace("T", " ")


def format_date(dt_str: str) -> str:
    """Преобразует ISO-дату 'ГГГГ-ММ-ДД' в 'ДД.ММ.ГГГГ'."""
    if not dt_str:
        return ""
    try:
        dt = datetime.strptime(dt_str.split("T")[0], "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return dt_str


# ------------------------------------------------------------
# Валидация полей в реальном времени
# ------------------------------------------------------------

def validate_login(login: str) -> str | None:
    login = login.strip()
    if not login:
        return "Поле с * обязательно для заполнения"
    if len(login) < 3:
        return "Логин должен содержать минимум 3 символа"
    if not re.match(r'^[a-zA-Z0-9_-]+$', login):
        return "Допустимы только латиница, цифры, _ и -"
    return None


def validate_password(password: str) -> str | None:
    if not password:
        return "Поле с * обязательно для заполнения"
    if len(password) < 8:
        return "Пароль должен содержать минимум 8 символов"
    return None


def validate_name(name: str, field_name: str = "Поле", required: bool = True) -> str | None:
    name = name.strip()
    if required and not name:
        return "Поле с * обязательно для заполнения"
    if name:
        if len(name) < 2:
            return "Значение должно содержать минимум 2 символа"
        if not re.match(r'^[А-Яа-яЁё\-]+$', name):
            return "Допустимы только русские буквы и дефис"
    return None


def validate_phone(phone: str) -> str | None:
    if not phone:
        return None
    phone = phone.strip()
    if not re.match(r'^[0-9+\-\(\) ]+$', phone):
        return "Допустимы только цифры, +, -, (, ), пробел"
    if len(phone) < 7:
        return "Номер должен содержать минимум 7 символов"
    if len(phone) > 20:
        return "Номер не может превышать 20 символов"
    return None


def validate_year_str(year_str: str) -> str | None:
    if not year_str:
        return None
    if not year_str.isdigit():
        return "Значение должно быть числом"
    year = int(year_str)
    from datetime import date
    current_year = date.today().year
    if year < 1 or year > current_year:
        return f"Год должен быть от 1 до {current_year}"
    return None


def validate_isbn(isbn: str) -> str | None:
    if not isbn:
        return None
    if not re.match(r'^\d{10,13}$', isbn.strip()):
        return "ISBN должен содержать от 10 до 13 цифр"
    return None


def validate_required(text: str, field_name: str = "Поле") -> str | None:
    if not text or not text.strip():
        return "Поле c * обязательно для заполнения"
    return None


def validate_positive_int(value: str, field_name: str = "Значение") -> str | None:
    if not value:
        return "Поле c * обязательно для заполнения"
    try:
        v = int(value)
        if v <= 0:
            return "Значение должно быть больше 0"
    except ValueError:
        return "Значение должно быть числом"
    return None


def validate_date_str(date_str: str, field_name: str = "Дата") -> str | None:
    """Проверяет дату в формате ДД.ММ.ГГГГ."""
    if not date_str or not date_str.strip():
        return "Поле обязательно для заполнения"
    try:
        from datetime import datetime, date
        dt = datetime.strptime(date_str.strip(), "%d.%m.%Y")
        d = dt.date()
        if d < date.today():
            return "Дата возврата не может быть раньше текущей даты"
        if d > date(date.today().year + 5, 12, 31):
            return "Максимальный срок 5 лет вперёд"
    except ValueError:
        return "Неверный формат. Используйте ДД.ММ.ГГГГ"
    return None


def validate_reader_card_id(card_id: str) -> str | None:
    card_id = card_id.strip()
    if not card_id:
        return "Поле с * обязательно для заполнения"
    if not re.match(r'^\d{7}$', card_id):
        return "Номер билета должен содержать ровно 7 цифр"
    return None


# ------------------------------------------------------------
# Bool-валидаторы для add_live_validation (возвращают True/False)
# ------------------------------------------------------------

def v_login(val: str) -> bool:
    return validate_login(val) is None


def v_password(val: str) -> bool:
    return validate_password(val) is None


def v_name(val: str) -> bool:
    return validate_name(val) is None


def v_name_optional(val: str) -> bool:
    return validate_name(val, required=False) is None


def v_phone(val: str) -> bool:
    return validate_phone(val) is None


def v_year(val: str) -> bool:
    return validate_year_str(val) is None


def v_isbn(val: str) -> bool:
    return validate_isbn(val) is None


def v_required(val: str) -> bool:
    return validate_required(val) is None


def v_positive_int(val: str) -> bool:
    return validate_positive_int(val) is None


def v_reader_card(val: str) -> bool:
    return validate_reader_card_id(val) is None


def add_live_validation_with_hint(widget, validator, hint_label, error_color="#c62828", normal_color="#d0d7de"):
    """Живая валидация с текстом ошибки под полем.
    validator(val) -> сообщение об ошибке (str) или None.
    Пустое поле не считается ошибкой — подсказка скрывается.
    Ошибка показывается только при потере фокуса, чтобы не мешать набору."""
    def _check(_event=None):
        val = widget.get()
        if not val or not val.strip():
            widget.configure(border_color=normal_color)
            hint_label.configure(text="")
            return
        err = validator(val)
        widget.configure(border_color=error_color if err else normal_color)
        hint_label.configure(text=err or "")
    widget.bind("<FocusOut>", _check)


# ------------------------------------------------------------
# Сортировка Treeview по клику на заголовок
# ------------------------------------------------------------
def sort_treeview(tree, col, reverse=False):
    """Сортирует строки Treeview по указанному столбцу."""
    data = [(tree.set(child, col), child) for child in tree.get_children("")]

    def _key(val):
        v = val[0]
        try:
            return (0, int(v))
        except Exception:
            try:
                return (1, float(v))
            except Exception:
                return (2, v.lower())

    data.sort(key=_key, reverse=reverse)
    for index, (_, child) in enumerate(data):
        tree.move(child, "", index)


# ------------------------------------------------------------
# Асинхронный вызов с колбэками (tkinter-friendly)
# ------------------------------------------------------------
def run_async(master, func, on_success=None, on_error=None):
    """Запускает func в отдельном потоке и вызывает колбэки в главном потоке."""
    def wrapper():
        try:
            result = func()
            if on_success:
                master.after(0, lambda: on_success(result))
        except Exception as e:
            print(f"[run_async error] {e}")
            if on_error:
                master.after(0, lambda err=e: on_error(err))

    threading.Thread(target=wrapper, daemon=True).start()
