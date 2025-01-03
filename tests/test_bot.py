# tests/test_bot.py

import pytest
import os
import sys

# Чтобы не ломать окружение, установим тестовый токен:
os.environ["TELEGRAM_BOT_TOKEN"] = "1234567:FAKE_TELEGRAM_TOKEN_EXAMPLE"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.append(PARENT_DIR)

from main import AITelegramBot

@pytest.mark.asyncio
async def test_bot_init():
    """
    Проверяем, что бот корректно инициализируется с тестовым токеном.
    """
    bot = AITelegramBot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    assert bot.bot is not None
    assert bot.dp is not None
    assert bot.plugin_manager is not None

    # Проверим, что плагины загрузились
    # (зависит от того, есть ли хотя бы один плагин в папке plugins)
    commands = bot.plugin_manager.get_available_commands()
    # Здесь нельзя угадать точное число, но проверим, что возвращается list
    assert isinstance(commands, list)

