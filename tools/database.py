# tools/database.py

import sqlite3
from typing import Optional, Tuple

class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.setup_tables()

    def setup_tables(self):
        # Пример таблицы для хранения пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                completed_practices INTEGER DEFAULT 0,
                reminder_time TEXT,
                timezone TEXT
            )
        ''')
        self.connection.commit()

    def get_user(self, user_id: int) -> Optional[Tuple]:
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()

    def add_or_update_user(self, user_id: int, completed_practices: int = 0, reminder_time: Optional[str] = None, timezone: Optional[str] = None):
        if self.get_user(user_id):
            self.cursor.execute('''
                UPDATE users
                SET completed_practices = ?, reminder_time = ?, timezone = ?
                WHERE user_id = ?
            ''', (completed_practices, reminder_time, timezone, user_id))
        else:
            self.cursor.execute('''
                INSERT INTO users (user_id, completed_practices, reminder_time, timezone)
                VALUES (?, ?, ?, ?)
            ''', (user_id, completed_practices, reminder_time, timezone))
        self.connection.commit()

    def close(self):
        self.connection.close()

# Singleton экземпляр базы данных
database = Database()
