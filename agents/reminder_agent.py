# agents/reminder_agent.py

from agents.base_agent import BaseAgent
from aiogram.types import Message
from datetime import datetime, timedelta
import re
from zoneinfo import ZoneInfo
import asyncio

class ReminderAgent(BaseAgent):
    """
    Агент для управления напоминаниями.
    """

    def get_name(self) -> str:
        return "reminder"

    def get_description(self) -> str:
        return "Установка напоминаний. Использование: /reminder ЧЧ:ММ [описание]"

    def _parse_time(self, time_str: str) -> tuple[str, str]:
        """Парсит время из разных форматов."""
        # Remove any 'Час:' prefix
        time_str = time_str.replace('Час:', '').strip()
        
        # Try to extract time in HH:MM format
        time_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
        if not time_match:
            return None, "Неверный формат времени. Пожалуйста, используйте ЧЧ:ММ, например, 09:00."

        hours, minutes = map(int, time_match.groups())
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            return None, "Неверное время. Часы должны быть от 0 до 23, минуты от 0 до 59."

        time_str = f"{hours:02d}:{minutes:02d}"
        description = time_str.join(re.split(r'\d{1,2}:\d{2}', time_str, 1)).strip()
        
        return time_str, description

    def _is_future_time(self, time_str: str, timezone: str = "Europe/Moscow") -> bool:
        """Проверяет, что время находится в будущем."""
        now = datetime.now(ZoneInfo(timezone))
        reminder_time = datetime.strptime(time_str, "%H:%M").replace(
            year=now.year, 
            month=now.month, 
            day=now.day,
            tzinfo=now.tzinfo
        )
        
        if reminder_time < now:
            reminder_time += timedelta(days=1)
            
        return reminder_time > now

    async def handle(self, args: str, message: Message) -> str:
        if not args:
            return "Пожалуйста, укажите время и описание напоминания. Например: /reminder 09:00 Встреча"

        user_id = message.from_user.id
        time_str, description = self._parse_time(args)
        
        if not time_str:
            return description  # Error message from _parse_time

        user_data = self.tools['database'].get_user_data(user_id)
        timezone = user_data.get('timezone', 'Europe/Moscow') if user_data else 'Europe/Moscow'

        if not self._is_future_time(time_str, timezone):
            return "Время напоминания уже прошло. Пожалуйста, укажите время в будущем."

        self.tools['database'].add_or_update_user(
            user_id=user_id,
            reminder_time=time_str,
            reminder_description=description,
            timezone=timezone
        )

        return f"Напоминание установлено на {time_str}: {description}"

    async def set_reminder(self, args: str, user_id: int, message: Message) -> str:
        if not args:
            return "Пожалуйста, укажите время для напоминания в формате ЧЧ:ММ. Пример: /reminder 09:00"

        # Clean up and extract time and description
        parts = args.strip().split(maxsplit=1)
        time_str = parts[0].strip()  # Remove any extra whitespace
        description = parts[1] if len(parts) > 1 else ""

        # Clean up time string from any extra words
        time_parts = time_str.split(':')
        if len(time_parts) == 2:
            # If we found a colon, take the surrounding digits as the time
            hour_part = ''.join(c for c in time_parts[0] if c.isdigit())[-2:]
            minute_part = ''.join(c for c in time_parts[1] if c.isdigit())[:2]
            time_str = f"{hour_part}:{minute_part}"
        else:
            return "Неверный формат времени. Пожалуйста, используйте ЧЧ:ММ, например, 09:00."

        try:
            reminder_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return f"Неверный формат времени '{time_str}'. Пожалуйста, используйте ЧЧ:ММ, например, 09:00."

        # Check if the reminder is for today
        now = datetime.now()
        if reminder_time < now.time():
            return "Время напоминания уже прошло. Пожалуйста, укажите время в будущем."

        return await self._save_reminder(user_id, time_str, description)

    async def list_reminders(self, user_id: int) -> str:
        user_data = self.tools['database'].get_user(user_id)
        if not user_data or not user_data[2]: 
            return "У вас нет установленных напоминаний."
        
        reminder_time = user_data[2]
        reminder_description = user_data[3] if user_data[3] else "Без описания"
        return f"Ваше текущее напоминание установлено на {reminder_time}. Описание: {reminder_description}"

    async def delete_reminder(self, user_id: int) -> str:
        try:
            user_data = self.tools['database'].get_user(user_id)
            if not user_data or not user_data[2]:
                return "У вас нет установленных напоминаний."

            # Удаляем напоминание из БД
            self.tools['database'].add_or_update_user(
                user_id=user_id,
                completed_practices=user_data[1],
                reminder_time=None,
                reminder_description=None,  # Ensure this field is set to None
                timezone=user_data[4]  # Correctly handle the timezone field
            )

            # Удаляем задачу из планировщика
            scheduler = self.tools.get('scheduler')
            if scheduler:
                scheduler.remove_job(f"reminder_{user_id}")

            return "Напоминание успешно удалено."
        except Exception as e:
            return f"Произошла ошибка при удалении напоминания: {e}"

    async def handle_edit_reminder(self, args: str, user_id: int) -> str:
        if not args:
            return "Пожалуйста, укажите новое время для напоминания в формате ЧЧ:ММ. Пример: /edit_reminder 09:00"

        parts = args.strip().split(maxsplit=1)
        time_str = parts[0]
        description = parts[1] if len(parts) > 1 else ""

        try:
            reminder_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return "Неверный формат времени. Пожалуйста, используйте ЧЧ:ММ, например, 09:00."

        return await self._save_reminder(user_id, time_str, description)

    async def _save_reminder(self, user_id: int, time_str: str, description: str) -> str:
        try:
            reminder_time = datetime.strptime(time_str, "%H:%M").time()
            user_data = self.tools['database'].get_user(user_id)
            
            # Сохранение в БД
            if user_data:
                self.tools['database'].add_or_update_user(
                    user_id=user_id,
                    completed_practices=user_data[1],
                    reminder_time=time_str,
                    reminder_description=description,
                    timezone=user_data[4]  # Correctly handle the timezone field
                )
            else:
                self.tools['database'].add_or_update_user(
                    user_id=user_id,
                    completed_practices=0,
                    reminder_time=time_str,
                    reminder_description=description,
                    timezone="UTC"
                )

            # Обновление планировщика
            scheduler = self.tools.get('scheduler')
            if not scheduler:
                return "Внутренняя ошибка: Планировщик задач не доступен."

            def send_reminder():
                asyncio.create_task(self.send_reminder_message(user_id, description))

            scheduler.add_job(
                send_reminder,
                'cron',
                hour=reminder_time.hour,
                minute=reminder_time.minute,
                id=f"reminder_{user_id}",
                replace_existing=True
            )

            return f"Напоминание установлено на {time_str} каждый день. Описание: {description}"
        except Exception as e:
            return f"Произошла ошибка при установке напоминания: {e}"

    async def send_reminder_message(self, user_id: int, description: str):
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
            message = "Это ваше ежедневное напоминание!"
            if description:
                message += f"\nОписание: {description}"
            await bot.send_message(user_id, message)
        except Exception as e:
            if logger:
                logger.error(f"Не удалось отправить напоминание пользователю {user_id}: {e}")
