from agents.base_agent import BaseAgent
from aiogram.types import Message
from datetime import datetime

class DateTimeAgent(BaseAgent):
    """
    Агент для решения задач, связанных с датой и временем.
    """

    def get_name(self) -> str:
        """
        Возвращает уникальное имя агента.
        """
        return "datetime"

    def get_description(self) -> str:
        """
        Короткое описание функционала.
        """
        return "Предоставляет информацию о текущей дате и времени."

    async def handle(self, args: str, message: Message) -> str:
        """
        Логика обработки запроса о дате/времени.

        :param args: Аргументы, которые GPT может передавать (например, 'дата', 'время', 'сколько сейчас времени?' и т.п.).
        :param message: Объект сообщения из Telegram.
        :return: Текстовый ответ с датой/временем.
        """
        now = datetime.now()
        # Преобразуем аргументы к нижнему регистру для упрощения анализа
        args_lower = args.lower()

        # Если аргументов нет или они не содержат ключевых слов, вернём полную дату + время
        if not args_lower:
            return f"Текущая дата и время: {now.strftime('%Y-%m-%d %H:%M:%S')}"

        # Пример простой логики: проверяем, что запрашивает пользователь
        if "дата" in args_lower:
            return f"Сегодняшняя дата: {now.strftime('%Y-%m-%d')}"
        elif "время" in args_lower:
            return f"Текущее время: {now.strftime('%H:%M:%S')}"

        # По умолчанию отвечаем полной датой и временем
        return f"Сейчас: {now.strftime('%Y-%m-%d %H:%M:%S')}"