# plugins/tasks_plugin.py

from aiogram.types import Message
from .base_plugin import BasePlugin

class TasksPlugin(BasePlugin):
    """
    Пример плагина для управления списком задач.
    """

    def __init__(self):
        self.tasks = []

    def get_commands(self) -> list[str]:
        # Две команды: /taskadd <текст задачи>, /tasklist
        return ["taskadd", "tasklist"]

    async def handle_command(self, command: str, args: str, message: Message) -> str | None:
        if command == "taskadd":
            task_text = args.strip()
            if not task_text:
                return "Не указана задача. Используйте /taskadd <текст задачи>."
            self.tasks.append(task_text)
            return f"Задача добавлена: {task_text}"

        elif command == "tasklist":
            if not self.tasks:
                return "Список задач пуст."
            tasks_str = "\n".join([f"{idx + 1}. {task}" for idx, task in enumerate(self.tasks)])
            return f"Список задач:\n{tasks_str}"

        return None
