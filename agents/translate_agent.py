# agents/translate_agent.py

import os
from agents.base_agent import BaseAgent
from aiogram.types import Message
from typing import Dict, Any

class TranslateAgent(BaseAgent):
    """
    Агент для обработки команды /translate и перевода текста.
    """

    def __init__(self, tools: Dict[str, Any]):
        super().__init__(tools)
        self.api_key = os.getenv("TRANSLATE_API_KEY")
        if not self.api_key:
            raise ValueError("Переменная окружения TRANSLATE_API_KEY не установлена!")

    def get_name(self) -> str:
        return "translate"

    def get_description(self) -> str:
        return "Переводит заданный текст на указанный язык. Пример использования: /translate en Привет мир"

    async def handle(self, args: str, message: Message) -> str:
        if not args:
            return "Пожалуйста, укажите язык и текст для перевода. Пример: /translate en Привет мир"

        try:
            target_lang, text = args.split(maxsplit=1)
        except ValueError:
            return "Пожалуйста, укажите язык и текст для перевода. Пример: /translate en Привет мир"

        try:
            translated_text = await self.translate_text(text, target_lang)
            return translated_text
        except Exception as e:
            return f"Произошла ошибка при переводе: {e}"

    async def translate_text(self, text: str, target_lang: str) -> str:
        """
        Переводит текст с помощью внешнего API.
        Использует HTTPClient из инструментов.
        """
        http_client = self.tools.get('http_client')
        if not http_client:
            return "Внутренняя ошибка: HTTP клиент не доступен."

        url = "https://api-free.deepl.com/v2/translate"
        data = {
            'auth_key': self.api_key,
            'text': text,
            'target_lang': target_lang.upper()
        }

        try:
            response = await http_client.post(url, data=data)
            translated_text = response['translations'][0]['text']
            return translated_text
        except Exception as e:
            return f"Не удалось перевести текст: {e}"
