# agents/auto_gen_agent.py

import os
import re
from agents.base_agent import BaseAgent
from aiogram.types import Message

class AutoGenAgent(BaseAgent):
    """
    Агент, умеющий генерировать файлы (например, новые агенты)
    и сохранять их в папку 'custom/'.
    """

    def get_name(self) -> str:
        return "autogen"

    def get_description(self) -> str:
        return (
            "Создаёт и сохраняет нужные файлы (например, новых агентов) "
            "в папке 'custom/'. Пример args:\n"
            "\"filename=some_agent.py; content=<код Python>\""
        )

    def _validate_agent_code(self, content: str) -> tuple[bool, str]:
        """Проверяет код агента на соответствие требованиям."""
        required_patterns = [
            (r'class \w+\(BaseAgent\):', "Класс должен наследоваться от BaseAgent"),
            (r'def get_name.*?return.*?', "Должен быть метод get_name"),
            (r'def get_description.*?return.*?', "Должен быть метод get_description"),
            (r'async def handle.*?', "Должен быть асинхронный метод handle")
        ]
        
        for pattern, error_msg in required_patterns:
            if not re.search(pattern, content, re.DOTALL):
                return False, error_msg
        return True, ""

    def _format_agent_code(self, filename: str, content: str) -> str:
        """Форматирует код агента в правильную структуру."""
        class_name = ''.join(word.capitalize() for word in filename[:-3].split('_'))
        
        template = f'''from agents.base_agent import BaseAgent
from aiogram.types import Message

class {class_name}(BaseAgent):
    def get_name(self) -> str:
        return "{filename[:-3]}"

    def get_description(self) -> str:
        return "Agent description"

    async def handle(self, args: str, message: Message) -> str:
        {content}
        return "Выполнено"
'''
        return template

    async def handle(self, args: str, message: Message) -> str:
        """
        Ожидается, что 'args' будет содержать, например:
        'filename=hello_agent.py; content=<код Python>'
        После чего агент создаст (или перезапишет) файл в папке 'custom/'.
        """
        # Парсим аргументы
        # Пример: filename=hello_agent.py; content=print("Hello")
        # Можно сделать более безопасный/сложный парсер, но для примера хватает простого
        if not args:
            return "Ошибка: аргументы не переданы. Формат: filename=..., content=..."
        
        # Разбиваем по точке с запятой
        parts = [part.strip() for part in args.split(";")]
        filename_part = None
        content_part = None
        
        for part in parts:
            if part.startswith("filename="):
                filename_part = part[len("filename="):].strip()
            elif part.startswith("content="):
                content_part = part[len("content="):].strip()

        if not filename_part or not content_part:
            return (
                "Ошибка: неверный формат аргументов.\n"
                "Пример: filename=some_agent.py; content=print('Hello')"
            )

        if not filename_part.endswith('.py'):
            return "Ошибка: файл должен иметь расширение .py"

        # Убираем потенциальные нежелательные символы (безопасность)
        # Например, уберём ../ и т.п.
        sanitized_filename = os.path.basename(filename_part)
        # Собираем полный путь
        file_path = os.path.join("custom", sanitized_filename)

        formatted_code = self._format_agent_code(sanitized_filename, content_part)
        is_valid, error_msg = self._validate_agent_code(formatted_code)
        
        if not is_valid:
            return f"Ошибка валидации кода: {error_msg}"

        # Создаём папку custom, если её нет
        os.makedirs("custom", exist_ok=True)

        try:
            # Записываем файл
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(formatted_code)

            return f"Файл '{sanitized_filename}' успешно сохранён в папке 'custom/'."
        except Exception as e:
            return f"Ошибка при сохранении файла: {e}"
