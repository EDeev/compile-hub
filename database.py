import sqlite3, json
from typing import Optional, List, Dict, Any
from datetime import datetime


class DBase:
    def __init__(self, db_path):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def init_db(self):
        with self.connection:
            # Таблица пользователей
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    username VARCHAR(20) UNIQUE NOT NULL,
                    password VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица файлов и папок
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(10) NOT NULL,
                    size VARCHAR(20),
                    folder_id INTEGER,
                    code TEXT,
                    code_lang VARCHAR(20),
                    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (folder_id) REFERENCES files(id) ON DELETE CASCADE
                )
            ''')

            # Таблица лимитов
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS limits (
                    user_id INTEGER PRIMARY KEY,
                    count_files INTEGER DEFAULT 0,
                    length_code INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

    # Пользователи
    def create_user(self, email: str, username: str, password: str) -> int:
        with self.connection:
            self.cursor.execute(
                "INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
                (email, username, password)
            )
            user_id = self.cursor.lastrowid

            # Создаём запись лимитов
            self.cursor.execute(
                "INSERT INTO limits (user_id, count_files, length_code) VALUES (?, 0, 0)",
                (user_id,)
            )
            return user_id

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        with self.connection:
            self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = self.cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self.connection:
            self.cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = self.cursor.fetchone()
            return dict(row) if row else None

    # Файлы
    def create_file(self, user_id: int, name: str, file_type: str, size: str,
                    folder_id: Optional[int] = None, code: Optional[str] = None,
                    code_lang: Optional[str] = None) -> int:
        with self.connection:
            self.cursor.execute('''
                INSERT INTO files (user_id, name, type, size, folder_id, code, code_lang, modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, file_type, size, folder_id, code, code_lang,
                  datetime.now().isoformat()))

            file_id = self.cursor.lastrowid

            # Обновляем лимиты
            if file_type == "file":
                self.cursor.execute(
                    "UPDATE limits SET count_files = count_files + 1 WHERE user_id = ?",
                    (user_id,)
                )
                if code:
                    self.cursor.execute(
                        "UPDATE limits SET length_code = length_code + ? WHERE user_id = ?",
                        (len(code), user_id)
                    )

            return file_id

    def get_user_files(self, user_id: int) -> List[Dict[str, Any]]:
        with self.connection:
            self.cursor.execute(
                "SELECT * FROM files WHERE user_id = ? ORDER BY type DESC, name",
                (user_id,)
            )
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]

    def get_file_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        with self.connection:
            self.cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None

    def update_file_folder(self, file_id: int, folder_id: Optional[int]):
        with self.connection:
            self.cursor.execute(
                "UPDATE files SET folder_id = ?, modified = ? WHERE id = ?",
                (folder_id, datetime.now().isoformat(), file_id)
            )

    def delete_file(self, file_id: int):
        with self.connection:
            # Получаем информацию о файле
            self.cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            file = self.cursor.fetchone()

            if file:
                file_dict = dict(file)
                user_id = file_dict["user_id"]

                # Если это файл, обновляем лимиты
                if file_dict["type"] == "file":
                    self.cursor.execute(
                        "UPDATE limits SET count_files = count_files - 1 WHERE user_id = ?",
                        (user_id,)
                    )
                    if file_dict["code"]:
                        self.cursor.execute(
                            "UPDATE limits SET length_code = length_code - ? WHERE user_id = ?",
                            (len(file_dict["code"]), user_id)
                        )

                # Удаляем файл
                self.cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))

                # Если это папка, удаляем все файлы в ней
                if file_dict["type"] == "folder":
                    self.cursor.execute("DELETE FROM files WHERE folder_id = ?", (file_id,))

    def get_user_limits(self, user_id: int) -> Dict[str, int]:
        with self.connection:
            self.cursor.execute("SELECT * FROM limits WHERE user_id = ?", (user_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else {"count_files": 0, "length_code": 0}

    # ЗАКРЫТИЕ ВЫЗОВА
    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()