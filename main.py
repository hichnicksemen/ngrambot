#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import pkgutil
import sys
import os
import importlib

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.client.bot import DefaultBotProperties

# Добавляем загрузку переменных окружения из .env
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Папка с плагинами
PLUGINS_FOLDER = os.path.join(os.path.dirname(__file__), 'plugins')

# --------------------- Менеджер плагинов ---------------------
class PluginManager:
    """
    Менеджер плагинов: хранит список команд и ассоциированных с ними плагинов.
    """

    def __init__(self):
        self.plugins = []
        self.command_map = {}

    def register_plugin(self, plugin_instance):
        """
        Регистрирует плагин, добавляя все его команды в command_map.
        """
        self.plugins.append(plugin_instance)
        for cmd in plugin_instance.get_commands():
            self.command_map[cmd.lower()] = plugin_instance

    def get_available_commands(self):
        """
        Возвращает список всех команд, зарегистрированных в системе.
        """
        return list(self.command_map.keys())

    async def handle_command(self, command: str, args: str, message: Message):
        """
        Находит, какой плагин умеет обрабатывать данную команду,
        и передаёт ей управление.
        """
        plugin = self.command_map.get(command.lower())
        if plugin:
            return await plugin.handle_command(command.lower(), args, message)
        else:
            return f"Неизвестная команда: /{command}"

# --------------------- Загрузка всех плагинов ---------------------
def load_plugins(plugin_manager: PluginManager):
    """
    Сканирует папку plugins, ищет модули, наследуемые от BasePlugin,
    и регистрирует их в plugin_manager.
    """
    sys.path.insert(0, PLUGINS_FOLDER)  # Чтобы Python мог импортировать из папки plugins

    for importer, module_name, ispkg in pkgutil.iter_modules([PLUGINS_FOLDER]):
        # Пропускаем __init__ и base_plugin
        if module_name in ("__init__", "base_plugin"):
            continue

        # Импортируем модуль
        full_module_name = f"plugins.{module_name}"
        module = importlib.import_module(full_module_name)

        # Ищем классы, унаследованные от BasePlugin
        base_plugin_class = None
        if hasattr(module, "BasePlugin"):
            # На случай, если кто-то внутри модуля переименовал класс
            base_plugin_class = module.BasePlugin

        # Если в модуле нет атрибута BasePlugin,
        # ищем в самом пакете plugins.base_plugin
        if not base_plugin_class:
            from plugins.base_plugin import BasePlugin
            base_plugin_class = BasePlugin

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            # Проверяем, что это класс, унаследованный от BasePlugin, но не сам BasePlugin
            if isinstance(attr, type) and issubclass(attr, base_plugin_class) and attr is not base_plugin_class:
                # Создаём экземпляр и регистрируем
                plugin_instance = attr()
                plugin_manager.register_plugin(plugin_instance)

# --------------------- Класс бота на aiogram3 ---------------------
class AITelegramBot:
    def __init__(self, token: str):
        self.bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode="HTML")
        )
        self.dp = Dispatcher()

        # Инициализируем менеджер плагинов
        self.plugin_manager = PluginManager()
        # Загружаем все плагины из папки plugins
        load_plugins(self.plugin_manager)

        # Регистрируем хендлер для команд
        @self.dp.message(F.text.startswith("/"))
        async def command_handler(message: Message):
            full_text = message.text
            parts = full_text.strip().split(maxsplit=1)
            cmd = parts[0].replace("/", "").lower()
            args = parts[1] if len(parts) > 1 else ""
            result = await self.plugin_manager.handle_command(cmd, args, message)
            if result:
                await message.answer(result)

        # Регистрируем хендлер для простых сообщений (без команды).
        @self.dp.message()
        async def text_handler(message: Message):
            # Место, где можно интегрировать AI (ChatGPT и т.п.)
            user_text = message.text
            await message.answer(f"AI-ответ (пока эхо): {user_text}")

    async def run(self):
        # Запускаем бота (long-polling)
        await self.dp.start_polling(self.bot)

# --------------------- Точка входа ---------------------
async def main():
    logging.basicConfig(level=logging.INFO)

    # Читаем токен бота из .env
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        raise ValueError("Переменная окружения TELEGRAM_BOT_TOKEN не установлена!")

    bot_app = AITelegramBot(token=telegram_token)
    await bot_app.run()

if __name__ == "__main__":
    asyncio.run(main())
