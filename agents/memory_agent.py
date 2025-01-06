# agents/memory_agent.py

from agents.base_agent import BaseAgent
from aiogram.types import Message
import logging

class MemoryAgent(BaseAgent):
    """
    Агент для управления памятью бота.
    Команды передаются в формате: 'command [text]', где command - это save/get/clear
    """

    def get_name(self) -> str:
        return "memory"

    def get_description(self) -> str:
        return (
            "Управление памятью бота. Вызов через аргументы:\n"
            "• get - получить сохраненные данные\n"
            "• save <текст> - сохранить новый текст\n"
            "• clear - очистить всю память"
        )

    async def handle(self, args: str, message: Message) -> str:
        user_id = message.from_user.id
        
        if not args:
            return "Пожалуйста, укажите команду (save/get/clear). Например: memory save <текст>"
        
        # Parse command and arguments
        parts = args.strip().split(maxsplit=1)
        command = parts[0].lower()
        context = parts[1] if len(parts) > 1 else ""

        # Simplify command parsing - remove all possible prefixes at once
        command = command.replace("memory_", "").replace("memory.", "").replace("memory ", "")
        
        try:
            if command == "save":
                if not context:
                    return "Пожалуйста, укажите текст для сохранения. Например: memory save <текст>"
                if self.tools['database'].save_memory(user_id, context):
                    return "✅ Контекст успешно сохранен"
                return "❌ Ошибка при сохранении контекста"
                
            elif command == "get":
                memories = self.tools['database'].get_memory(user_id)
                if memories:
                    return "📋 Последние воспоминания:\n" + "\n---\n".join(memories)
                return "📭 Память пуста"
                
            elif command == "clear":
                if self.tools['database'].clear_memory(user_id):
                    return "🗑 Память очищена"
                return "❌ Произошла ошибка при очистке памяти"
            
            return (
                "❓ Неизвестная команда. Используйте:\n"
                "• memory save <текст> - сохранить текст\n"
                "• memory get - показать сохраненное\n"
                "• memory clear - очистить память"
            )
            
        except Exception as e:
            logging.error(f"Ошибка в memory агенте: {str(e)}")
            return f"❌ Произошла ошибка: {str(e)}"
