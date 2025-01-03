# plugins/base_plugin.py

from aiogram.types import Message

class BasePlugin:
    """
    Базовый класс для всех плагинов.
    Каждый плагин должен:
    1) Возвращать список поддерживаемых команд (без слэша).
    2) Реализовать метод handle_command для обработки команд.
    """

    def get_commands(self) -> list[str]:
        """ Список команд, которые плагин обрабатывает, например ["search"]. """
        return []

    async def handle_command(self, command: str, args: str, message: Message) -> str | None:
        """
        Обрабатывает команду (command) с аргументами (args).
        Возвращает текст, который нужно отправить пользователю,
        либо None, если ответ уже отправлен или команда не распознана.
        """
        return None
