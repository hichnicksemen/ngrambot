# agents/base_agent.py

from abc import ABC, abstractmethod
from aiogram.types import Message
from typing import Dict, Any

class BaseAgent(ABC):
    """
    Абстрактный базовый класс для всех агентов.
    """

    def __init__(self, tools: Dict[str, Any]):
        """
        Инициализация агента с доступом к инструментам.
        """
        self.tools = tools

    @abstractmethod
    def get_name(self) -> str:
        """
        Возвращает имя агента.
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Возвращает описание агента.
        """
        pass

    @abstractmethod
    async def handle(self, args: str, message: Message) -> str:
        """
        Обрабатывает запрос и возвращает ответ.
        """
        pass