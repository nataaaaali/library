from db import get_connection
from datetime import date


def _row_to_dict(cursor, row):
    """Преобразует строку БД в словарь {имя_колонки: значение}."""
    if row is None:
        return None
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


# ------------------------------------------------------------
# Пользователи
# ------------------------------------------------------------

def get_user_by_login(login: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.*, r.name as role_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.login = %s
    """, (login,))
    result = _row_to_dict(cursor, cursor.fetchone())
    cursor.close()
    return result


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.*, r.name as role_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = %s
    """, (user_id,))
    result = _row_to_dict(cursor, cursor.fetchone())
    cursor.close()
    return result


def save_user(user_data: dict) -> int:
    """Создаёт пользователя. Возвращает id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM roles WHERE name = %s", (user_data['role'],))
    role_id = cursor.fetchone()[0]
    
    cursor.execute("""
        INSERT INTO users (login, password_hash, last_name, first_name, middle_name, role_id)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
    """, (
        user_data['login'], user_data['password_hash'],
        user_data['last_name'], user_data['first_name'], user_data.get('middle_name'),
        role_id
    ))
    user_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    return user_id


def get_all_users() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.login, u.last_name, u.first_name, u.middle_name, r.name as role
        FROM users u
        JOIN roles r ON u.role_id = r.id
        ORDER BY u.id
    """)
    rows = cursor.fetchall()
    result = [_row_to_dict(cursor, row) for row in rows]
    cursor.close()
    return result


def delete_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    # Сохраняем историю операций, но обнуляем ссылки на удаляемого пользователя
    cursor.execute("UPDATE audit_logs SET user_id = NULL WHERE user_id = %s", (user_id,))
    cursor.execute("UPDATE rentals SET librarian_id = NULL WHERE librarian_id = %s", (user_id,))
    cursor.execute("UPDATE extension_records SET librarian_id = NULL WHERE librarian_id = %s", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()


# ------------------------------------------------------------
# Жанры
# ------------------------------------------------------------

def get_all_genres() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM genres ORDER BY name")
    rows = cursor.fetchall()
    result = [_row_to_dict(cursor, row) for row in rows]
    cursor.close()
    return result


def get_or_create_genre(name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM genres WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row:
        genre_id = row[0]
    else:
        cursor.execute("INSERT INTO genres (name) VALUES (%s) RETURNING id", (name,))
        genre_id = cursor.fetchone()[0]
        conn.commit()
    cursor.close()
    return genre_id


# ------------------------------------------------------------
# Статусы
# ------------------------------------------------------------

def get_status_id(name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM statuses WHERE name = %s", (name,))
    status_id = cursor.fetchone()[0]
    cursor.close()
    return status_id


def get_all_statuses() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM statuses ORDER BY id")
    rows = cursor.fetchall()
    result = [_row_to_dict(cursor, row) for row in rows]
    cursor.close()
    return result


# ------------------------------------------------------------
# Книги
# ------------------------------------------------------------

def get_book_by_id(book_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, b.title, b.author, b.year, b.isbn,
               g.name as genre, b.location, s.name as status
        FROM books b
        LEFT JOIN genres g ON b.genre_id = g.id
        JOIN statuses s ON b.status_id = s.id
        WHERE b.id = %s
    """, (book_id,))
    result = _row_to_dict(cursor, cursor.fetchone())
    cursor.close()
    return result


def get_all_books() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, b.title, b.author, b.year, b.isbn,
               g.name as genre, b.location, s.name as status
        FROM books b
        LEFT JOIN genres g ON b.genre_id = g.id
        JOIN statuses s ON b.status_id = s.id
        ORDER BY b.id
    """)
    rows = cursor.fetchall()
    result = [_row_to_dict(cursor, row) for row in rows]
    cursor.close()
    return result


def save_book(book_data: dict) -> int:
    """Создаёт книгу. Возвращает id."""
    conn = get_connection()
    cursor = conn.cursor()
    
    genre_id = None
    if book_data.get('genre'):
        genre_id = get_or_create_genre(book_data['genre'])
    
    status_id = get_status_id(book_data['status'])
    
    cursor.execute("""
        INSERT INTO books (title, author, year, isbn, genre_id, location, status_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (
        book_data['title'], book_data['author'], book_data.get('year'),
        book_data.get('isbn'), genre_id, book_data.get('location'),
        status_id
    ))
    book_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    return book_id


def update_book_status(book_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    status_id = get_status_id(status)
    cursor.execute("""
        UPDATE books SET status_id = %s WHERE id = %s
    """, (status_id, book_id))
    conn.commit()
    cursor.close()


def update_book(book_id: int, book_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    
    genre_id = None
    if book_data.get('genre'):
        genre_id = get_or_create_genre(book_data['genre'])
    
    status_id = get_status_id(book_data['status']) if book_data.get('status') else None
    
    cursor.execute("""
        UPDATE books SET title = %s, author = %s, year = %s, isbn = %s,
            genre_id = %s, location = %s, status_id = COALESCE(%s, status_id)
        WHERE id = %s
    """, (
        book_data['title'], book_data['author'], book_data.get('year'),
        book_data.get('isbn'), genre_id, book_data.get('location'),
        status_id, book_id
    ))
    conn.commit()
    cursor.close()


def count_rentals_for_book(book_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rentals WHERE book_id = %s", (book_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    return count


def get_active_rental_for_book(book_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM rentals
        WHERE book_id = %s AND actual_return_date IS NULL
        LIMIT 1
    """, (book_id,))
    result = _row_to_dict(cursor, cursor.fetchone())
    cursor.close()
    return result


def delete_book(book_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
    conn.commit()
    cursor.close()


# ------------------------------------------------------------
# Читательские билеты
# ------------------------------------------------------------

def generate_reader_card_id() -> str:
    """Генерирует следующий 7-значный номер билета."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM reader_cards")
    row = cursor.fetchone()
    cursor.close()
    
    max_id = row[0]
    if max_id is None:
        next_num = 1
    else:
        next_num = int(max_id) + 1
    return f"{next_num:07d}"


def get_reader_card(card_id: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reader_cards WHERE id = %s", (card_id,))
    result = _row_to_dict(cursor, cursor.fetchone())
    cursor.close()
    return result


def get_all_reader_cards() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reader_cards ORDER BY id")
    rows = cursor.fetchall()
    result = [_row_to_dict(cursor, row) for row in rows]
    cursor.close()
    return result


def save_reader_card(reader_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reader_cards (id, last_name, first_name, middle_name, phone, expiration_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        reader_data['id'], reader_data['last_name'], reader_data['first_name'],
        reader_data.get('middle_name'), reader_data.get('phone'),
        reader_data['expiration_date']
    ))
    conn.commit()
    cursor.close()


def update_reader_card(card_id: str, updates: dict):
    conn = get_connection()
    cursor = conn.cursor()
    
    allowed = ['last_name', 'first_name', 'middle_name', 'phone', 'expiration_date']
    fields = []
    values = []
    for key, value in updates.items():
        if key in allowed:
            fields.append(f"{key} = %s")
            values.append(value)
    
    if fields:
        sql = f"UPDATE reader_cards SET {', '.join(fields)} WHERE id = %s"
        values.append(card_id)
        cursor.execute(sql, values)
        conn.commit()
    cursor.close()


def delete_reader_card(card_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reader_cards WHERE id = %s", (card_id,))
    conn.commit()
    cursor.close()


# ------------------------------------------------------------
# Аренда
# ------------------------------------------------------------

def get_rental_by_id(rental_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, b.title as book_title, rc.last_name || ' ' || rc.first_name || COALESCE(' ' || rc.middle_name, '') as reader_name
        FROM rentals r
        JOIN books b ON r.book_id = b.id
        JOIN reader_cards rc ON r.reader_card_id = rc.id
        WHERE r.id = %s
    """, (rental_id,))
    result = _row_to_dict(cursor, cursor.fetchone())
    cursor.close()
    return result


def get_all_rentals(active_only: bool = False) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        SELECT r.*, b.title as book_title, rc.last_name || ' ' || rc.first_name || COALESCE(' ' || rc.middle_name, '') as reader_name
        FROM rentals r
        JOIN books b ON r.book_id = b.id
        JOIN reader_cards rc ON r.reader_card_id = rc.id
    """
    if active_only:
        sql += " WHERE r.actual_return_date IS NULL"
    sql += " ORDER BY r.id DESC"
    cursor.execute(sql)
    rows = cursor.fetchall()
    result = [_row_to_dict(cursor, row) for row in rows]
    cursor.close()
    return result


def create_rental(rental_data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rentals (book_id, reader_card_id, librarian_id, issue_date, due_date)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """, (
        rental_data['book_id'], rental_data['reader_card_id'],
        rental_data['librarian_id'], rental_data['issue_date'],
        rental_data['due_date']
    ))
    rental_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    return rental_id


def close_rental(rental_id: int, actual_return_date: date, fine_amount: float, is_overdue: bool):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE rentals
        SET actual_return_date = %s, fine_amount = %s, is_overdue = %s
        WHERE id = %s
    """, (actual_return_date, fine_amount, is_overdue, rental_id))
    conn.commit()
    cursor.close()


def update_rental_due_date(rental_id: int, new_due_date: date):
    conn = get_connection()
    cursor = conn.cursor()
    # При продлении сбрасываем флаг просрочки и штраф — книга получает новый срок
    cursor.execute("""
        UPDATE rentals SET due_date = %s, is_overdue = FALSE, fine_amount = 0.00 WHERE id = %s
    """, (new_due_date, rental_id))
    conn.commit()
    cursor.close()


# ------------------------------------------------------------
# Продление аренды
# ------------------------------------------------------------

def create_extension(ext_data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO extension_records (rental_id, extension_date, new_due_date, librarian_id)
        VALUES (%s, %s, %s, %s) RETURNING id
    """, (
        ext_data['rental_id'], ext_data['extension_date'],
        ext_data['new_due_date'], ext_data['librarian_id']
    ))
    ext_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    return ext_id


def get_extensions_by_rental(rental_id: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM extension_records WHERE rental_id = %s ORDER BY extension_date
    """, (rental_id,))
    rows = cursor.fetchall()
    result = [_row_to_dict(cursor, row) for row in rows]
    cursor.close()
    return result


# ------------------------------------------------------------
# Логи аудита
# ------------------------------------------------------------

def log_event(user_id: int | None, action: str, details: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (user_id, action, details)
        VALUES (%s, %s, %s)
    """, (user_id, action, details))
    conn.commit()
    cursor.close()


def get_audit_logs(limit: int = 50, offset: int = 0, action: str = None,
                    user_query: str = None, date_from: str = None, date_to: str = None) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    conditions = []
    params = []
    if action:
        conditions.append("al.action = %s")
        params.append(action)
    if user_query:
        conditions.append("(u.last_name ILIKE %s OR u.first_name ILIKE %s OR u.login ILIKE %s)")
        params.extend([f"%{user_query}%", f"%{user_query}%", f"%{user_query}%"])
    if date_from:
        conditions.append("al.created_at >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("al.created_at < (%s::date + interval '1 day')")
        params.append(date_to)
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"""
        SELECT al.*,
               CASE
                   WHEN u.last_name IS NOT NULL THEN
                       u.last_name || ' ' || u.first_name || COALESCE(' ' || u.middle_name, '')
                   ELSE 'Система'
               END as user_display
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        {where_clause}
        ORDER BY al.created_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    result = [_row_to_dict(cursor, row) for row in rows]
    cursor.close()
    return result


def count_audit_logs(action: str = None, user_query: str = None,
                     date_from: str = None, date_to: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    conditions = []
    params = []
    if action:
        conditions.append("al.action = %s")
        params.append(action)
    if user_query:
        conditions.append("(u.last_name ILIKE %s OR u.first_name ILIKE %s OR u.login ILIKE %s)")
        params.extend([f"%{user_query}%", f"%{user_query}%", f"%{user_query}%"])
    if date_from:
        conditions.append("al.created_at >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("al.created_at < (%s::date + interval '1 day')")
        params.append(date_to)
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"""
        SELECT COUNT(*) FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        {where_clause}
    """
    cursor.execute(sql, tuple(params))
    count = cursor.fetchone()[0]
    cursor.close()
    return count
