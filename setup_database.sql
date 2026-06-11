-- Справочник ролей
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);
INSERT INTO roles (name) VALUES ('admin'), ('librarian') ON CONFLICT DO NOTHING;

-- Справочник статусов книг
CREATE TABLE IF NOT EXISTS statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);
INSERT INTO statuses (name) VALUES ('В наличии'), ('Выдана'), ('Утрачена') ON CONFLICT DO NOTHING;

-- Справочник жанров
CREATE TABLE IF NOT EXISTS genres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Пользователи (раздельное ФИО)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    role_id INT REFERENCES roles(id) NOT NULL
);

-- Читательские билеты (7-значный номер с ведущими нулями)
CREATE TABLE IF NOT EXISTS reader_cards (
    id VARCHAR(7) PRIMARY KEY,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    phone VARCHAR(20),
    issue_date DATE DEFAULT CURRENT_DATE,
    expiration_date DATE NOT NULL
);

-- Книги
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    year INT CHECK (year >= 1 AND year <= 2100),
    isbn VARCHAR(20),
    genre_id INT REFERENCES genres(id),
    location VARCHAR(100),
    status_id INT REFERENCES statuses(id) NOT NULL
);

-- Аренда
CREATE TABLE IF NOT EXISTS rentals (
    id SERIAL PRIMARY KEY,
    book_id INT REFERENCES books(id) NOT NULL,
    reader_card_id VARCHAR(7) REFERENCES reader_cards(id) NOT NULL,
    librarian_id INT REFERENCES users(id) ON DELETE SET NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    actual_return_date DATE,
    is_overdue BOOLEAN DEFAULT FALSE,
    fine_amount DECIMAL(10,2) DEFAULT 0.00
);

-- Продление аренды
CREATE TABLE IF NOT EXISTS extension_records (
    id SERIAL PRIMARY KEY,
    rental_id INT REFERENCES rentals(id) ON DELETE CASCADE NOT NULL,
    extension_date DATE NOT NULL,
    new_due_date DATE NOT NULL,
    librarian_id INT REFERENCES users(id) ON DELETE SET NULL
);

-- Логи аудита
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Тестовый администратор (пароль: admin123)
-- Хэш сгенерирован bcrypt (cost=12)
INSERT INTO users (login, password_hash, last_name, first_name, middle_name, role_id)
VALUES ('admin', '$2b$12$xoHVdQyGySn2M.vRMN59GOqLJJSi2ao/BaEbAbxq9r.05qyIC4v0O', 'Администратор', 'Системы', NULL,
        (SELECT id FROM roles WHERE name = 'admin'))
ON CONFLICT (login) DO NOTHING;


