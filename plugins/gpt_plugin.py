# plugins/gpt_plugin.py

import openai
import os
from plugins.base_plugin import BasePlugin
from aiogram.types import Message

class GPTPlugin(BasePlugin):
    """
    Плагин для обработки команды /gpt и взаимодействия с OpenAI GPT.
    """

    def __init__(self):
        # Загрузка ключа API из переменных окружения
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Переменная окружения OPENAI_API_KEY не установлена!")
        openai.api_key = self.api_key

    def get_commands(self):
        """
        Возвращает список команд, которые обрабатывает этот плагин.
        """
        return ['gpt']

    async def handle_command(self, command: str, args: str, message: Message):
        """
        Обрабатывает команду /gpt.
        """
        if command == 'gpt':
            if not args:
                return "Пожалуйста, введите вопрос после команды. Пример: /gpt Расскажи мне анекдот."
            
            try:
                response = await self.get_gpt_response(args)
                return response
            except Exception as e:
                return f"Произошла ошибка при обращении к GPT: {e}"
        
        return "Неизвестная команда для GPTPlugin."

    async def get_gpt_response(self, prompt: str):
        """
        Получает ответ от OpenAI GPT на заданный prompt с использованием ChatCompletion API.
        """
        try:
            completion = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Вы — полезный помощник."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.7,
            )
            response_text = completion.choices[0].message['content'].strip()
            return response_text
        except Exception as e:
            raise e