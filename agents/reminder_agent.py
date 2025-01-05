# agents/reminder_agent.py

from agents.base_agent import BaseAgent
from aiogram.types import Message
from datetime import datetime
import asyncio

class ReminderAgent(BaseAgent):
    """
    Агент для установки напоминаний.
    Обрабатывает команду /reminder <время>
    """

    def get_name(self) -> str:
        return "reminder"

    def get_description(self) -> str:
        return "Устанавливает ежедневное напоминание в указанное время. Пример использования: /reminder 09:00"

    async def handle(self, args: str, message: Message) -> str:
        if not args:
            return "Пожалуйста, укажите время для напоминания в формате ЧЧ:ММ. Пример: /reminder 09:00"

        time_str = args.strip()
        # Валидация времени
        try:
            reminder_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return "Неверный формат времени. Пожалуйста, используйте ЧЧ:ММ, например, 09:00."

        user_id = message.from_user.id

        try:
            # Сохранение напоминания в базе данных
            user_data = self.tools['database'].get_user(user_id)
            if user_data:
                self.tools['database'].add_or_update_user(user_id=user_id, completed_practices=user_data[1], reminder_time=time_str, timezone=user_data[3])
            else:
                self.tools['database'].add_or_update_user(user_id=user_id, completed_practices=0, reminder_time=time_str, timezone="UTC")

            # Установка задачи в планировщике
            scheduler = self.tools.get('scheduler')
            if not scheduler:
                return "Внутренняя ошибка: Планировщик задач не доступен."

            def send_reminder():
                asyncio.create_task(self.send_reminder_message(user_id))

            scheduler.add_job(send_reminder, 'cron', hour=reminder_time.hour, minute=reminder_time.minute, id=f"reminder_{user_id}", replace_existing=True)

            return f"Напоминание установлено на {time_str} каждый день."
        except Exception as e:
            return f"Произошла ошибка при установке напоминания: {e}"

    async def send_reminder_message(self, user_id: int):
        """
        Отправляет напоминание пользователю.
        """
        bot = self.tools.get('bot')
        logger = self.tools.get('logger')
        if not bot:
            if logger:
                logger.error("Инструмент 'bot' не доступен.")
            return

        try:
            await bot.send_message(user_id, "Это ваше ежедневное напоминание!")
        except Exception as e:
            if logger:
                logger.error(f"Не удалось отправить напоминание пользователю {user_id}: {e}")
