# plugins/search_plugin.py

from aiogram.types import Message
from .base_plugin import BasePlugin

class SearchPlugin(BasePlugin):
    """
    Пример плагина, выполняющего некий «поиск».
    """

    def get_commands(self) -> list[str]:
        # Плагин умеет обрабатывать одну команду: /search
        return ["search"]

    async def handle_command(self, command: str, args: str, message: Message) -> str | None:
        if command == "search":
            query = args.strip()
            # Здесь можно реализовать реальный поиск (Google, Bing, др. API).
            return f"Ищу информацию по запросу: {query}"
        return None
