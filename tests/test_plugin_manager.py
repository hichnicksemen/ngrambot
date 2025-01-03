import pytest
import datetime
from aiogram.types import Message, Chat, User
from main import PluginManager

@pytest.mark.asyncio
async def test_plugin_manager():
    plugin_manager = PluginManager()

    # Тестовый плагин
    class MockPlugin:
        def get_commands(self):
            return ["hello", "bye"]
        async def handle_command(self, command: str, args: str, message: Message):
            if command == "hello":
                return "Hello from MockPlugin!"
            elif command == "bye":
                return "Goodbye from MockPlugin!"
            return None

    mock_plugin = MockPlugin()
    plugin_manager.register_plugin(mock_plugin)

    # Проверяем регистрацию команд
    commands = plugin_manager.get_available_commands()
    assert "hello" in commands
    assert "bye" in commands

    # Создаём тестовое "сообщение" с допустимыми значениями
    fake_message = Message(
        message_id=123,
        date=datetime.datetime.now(),        # Должна быть datetime, а не None
        chat=Chat(id=999, type="private"),   # Минимально допустимый объект чата
        from_user=User(id=456, is_bot=False, first_name="TestUser"),
        text=""                              # Можно оставить пустым, если вам не важно
    )

    # Проверяем обработку команды "hello"
    response_hello = await plugin_manager.handle_command("hello", "", fake_message)
    assert response_hello == "Hello from MockPlugin!"

    # Проверяем обработку команды "bye"
    response_bye = await plugin_manager.handle_command("bye", "", fake_message)
    assert response_bye == "Goodbye from MockPlugin!"

    # Проверяем неизвестную команду
    response_unknown = await plugin_manager.handle_command("unknown_cmd", "", fake_message)
    assert response_unknown == "Неизвестная команда: /unknown_cmd"
