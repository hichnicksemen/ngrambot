# agents/info_agent.py

from agents.base_agent import BaseAgent
from aiogram.types import Message
from typing import Dict, Any

class InfoAgent(BaseAgent):
    """
    Агент для обработки команды /info и предоставления информации о боте.
    """

    def __init__(self, tools: Dict[str, Any]):
        super().__init__(tools)

    def get_name(self) -> str:
        return "info"

    def get_description(self) -> str:
        return "Предоставляет информацию о боте. Пример использования: /info"

    async def handle(self, args: str, message: Message) -> str:
        return (
            "Этот бот использует GPT для общения и поддерживает плагины-агенты для расширения функциональности.\n\n"
            "Доступные команды:\n"
            "/weather <город> — Получить текущую погоду в указанном городе.\n"
            "/info — Получить информацию о боте.\n"
            "/help — Показать список доступных команд."
        )
