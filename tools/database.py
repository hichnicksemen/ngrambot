# tools/database.py

import sqlite3
import logging
from typing import Optional, Tuple

class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.setup_tables()
        logging.info(f"Подключение к базе данных {db_path} установлено.")

    def setup_tables(self):
        # Пример таблицы для хранения пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                completed_practices INTEGER DEFAULT 0,
                reminder_time TEXT,
                reminder_description TEXT,
                timezone TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                context TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.connection.commit()
        logging.info("Таблицы users и memory созданы или уже существуют.")

    def get_user(self, user_id: int) -> Optional[Tuple]:
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = self.cursor.fetchone()
        logging.info(f"Получены данные пользователя {user_id}: {user}")
        return user

    def get_user_data(self, user_id: int) -> Optional[dict]:
        user = self.get_user(user_id)
        if user:
            return {
                'user_id': user[0],
                'completed_practices': user[1],
                'reminder_time': user[2],
                'reminder_description': user[3],
                'timezone': user[4]
            }
        return None

    def add_or_update_user(self, user_id: int, completed_practices: int = 0, reminder_time: Optional[str] = None, reminder_description: Optional[str] = None, timezone: Optional[str] = None):
        if self.get_user(user_id):
            self.cursor.execute('''
                UPDATE users
                SET completed_practices = ?, reminder_time = ?, reminder_description = ?, timezone = ?
                WHERE user_id = ?
            ''', (completed_practices, reminder_time, reminder_description, timezone, user_id))
            logging.info(f"Обновлены данные пользователя {user_id}.")
        else:
            self.cursor.execute('''
                INSERT INTO users (user_id, completed_practices, reminder_time, reminder_description, timezone)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, completed_practices, reminder_time, reminder_description, timezone))
            logging.info(f"Добавлен новый пользователь {user_id}.")
        self.connection.commit()

    def delete_user(self, user_id: int) -> bool:
        try:
            self.cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            self.connection.commit()
            deleted = self.cursor.rowcount > 0
            logging.info(f"{'Удалены' if deleted else 'Не найдены'} данные пользователя {user_id}")
            return deleted
        except Exception as e:
            logging.error(f"Ошибка при удалении пользователя {user_id}: {e}")
            return False

    def save_memory(self, user_id: int, context: str) -> bool:
        try:
            self.cursor.execute('INSERT INTO memory (user_id, context) VALUES (?, ?)', 
                              (user_id, context))
            self.connection.commit()
            logging.info(f"Сохранен контекст для пользователя {user_id}: {context[:50]}...")
            return True
        except Exception as e:
            logging.error(f"Ошибка при сохранении контекста: {e}")
            return False

    def get_memory(self, user_id: int, limit: int = 5) -> list:
        try:
            self.cursor.execute('''
                SELECT context FROM memory 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?''', (user_id, limit))
            results = [row[0] for row in self.cursor.fetchall()]
            logging.info(f"Получено {len(results)} записей для пользователя {user_id}")
            return results
        except Exception as e:
            logging.error(f"Ошибка при получении контекста: {e}")
            return []

    def clear_memory(self, user_id: int) -> bool:
        try:
            # First check if user has any memories
            self.cursor.execute('SELECT COUNT(*) FROM memory WHERE user_id = ?', (user_id,))
            count = self.cursor.fetchone()[0]
            
            if count == 0:
                logging.info(f"Нет записей для очистки у пользователя {user_id}")
                return True  # Return True as there's nothing to clear
                
            self.cursor.execute('DELETE FROM memory WHERE user_id = ?', (user_id,))
            self.connection.commit()
            deleted = self.cursor.rowcount > 0
            logging.info(f"Удалено {self.cursor.rowcount} записей для пользователя {user_id}")
            return deleted
            
        except Exception as e:
            logging.error(f"Ошибка при очистке памяти пользователя {user_id}: {e}")
            return False

    def close(self):
        self.connection.close()
        logging.info("Соединение с базой данных закрыто.")

# Singleton экземпляр базы данных
database = Database()
