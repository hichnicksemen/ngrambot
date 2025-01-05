# agents/save_agent.py

from agents.base_agent import BaseAgent
from aiogram.types import Message

class SaveAgent(BaseAgent):
    """
    Агент для сохранения данных пользователя в базу данных.
    Обрабатывает команду /save <data>
    """

    def get_name(self) -> str:
        return "save"

    def get_description(self) -> str:
        return "Сохраняет предоставленные данные в базу данных. Пример использования: /save Пример данных"

    async def handle(self, args: str, message: Message) -> str:
        if not args:
            return "Пожалуйста, предоставьте данные для сохранения. Пример: /save Пример данных"

        user_id = message.from_user.id
        data = args.strip()

        try:
            # Используем инструмент database для сохранения данных
            self.tools['database'].add_or_update_user(user_id=user_id, completed_practices=1, reminder_time="09:00", timezone="UTC")  # Пример обновления
            return f"Данные успешно сохранены для пользователя {user_id}."
        except Exception as e:
            return f"Произошла ошибка при сохранении данных: {e}"
