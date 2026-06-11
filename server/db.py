# ============================================================
# Подключение к PostgreSQL (psycopg2)
# ============================================================

import psycopg2
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


class Database:
    """Простое соединение с PostgreSQL."""
    
    def __init__(self):
        self._connection = None
    
    def get_connection(self):
        """Возвращает соединение (создаёт новое, если нужно)."""
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
        return self._connection
    
    def close(self):
        """Закрывает соединение."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None


# Глобальный экземпляр
_db = Database()


def get_connection():
    """Глобальная функция для получения соединения."""
    return _db.get_connection()


def close_connection():
    """Закрыть глобальное соединение."""
    _db.close()
