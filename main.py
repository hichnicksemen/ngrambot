#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import pkgutil
import sys
import os
import importlib
import json
from typing import List, Dict, Any
from openai import AsyncOpenAI

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.client.bot import DefaultBotProperties

# Добавляем загрузку переменных окружения из .env
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env, если он существует
load_dotenv()

# Папки с плагинами и инструментами
AGENTS_FOLDER = os.path.join(os.path.dirname(__file__), 'agents')
TOOLS_FOLDER = os.path.join(os.path.dirname(__file__), 'tools')

# --------------------- Менеджер Агентов ---------------------
class AgentManager:
    """
    Менеджер агентов: хранит список агентов и ассоциированных с ними команд.
    """

    def __init__(self, tools: Dict[str, Any]):
        self.agents: List[Any] = []
        self.command_map: Dict[str, Any] = {}
        self.tools = tools  # Инструменты доступны для агентов

    def register_agent(self, agent_instance):
        """
        Регистрирует агента, добавляя все его команды в command_map.
        """
        self.agents.append(agent_instance)
        command = agent_instance.get_name().lower()
        self.command_map[command] = agent_instance

    def get_available_commands(self) -> List[str]:
        """
        Возвращает список всех команд, зарегистрированных в системе.
        """
        return list(self.command_map.keys())

    async def handle_command(self, command: str, args: str, message: Message) -> str:
        """
        Находит, какой агент умеет обрабатывать данную команду,
        и передаёт ему управление.
        """
        agent = self.command_map.get(command.lower())
        if agent:
            return await agent.handle(args, message)
        else:
            return f"Неизвестная команда: /{command}"

    def get_agents_info(self) -> List[Dict[str, str]]:
        """
        Возвращает информацию о всех агентах.
        """
        return [
            {
                "name": agent.get_name(),
                "description": agent.get_description()
            }
            for agent in self.agents
        ]

# --------------------- Загрузка всех Агентов ---------------------
def load_agents(agent_manager: AgentManager):
    """
    Сканирует папку plugins, ищет модули, наследуемые от BaseAgent,
    и регистрирует их в agent_manager.
    """
    sys.path.insert(0, AGENTS_FOLDER)  # Чтобы Python мог импортировать из папки plugins

    for importer, module_name, ispkg in pkgutil.iter_modules([AGENTS_FOLDER]):
        # Пропускаем __init__ и base_agent
        if module_name in ("__init__", "base_agent"):
            continue

        # Импортируем модуль
        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            logging.error(f"Не удалось импортировать модуль {module_name}: {e}")
            continue

        # Импортируем BaseAgent
        try:
            from agents.base_agent import BaseAgent
        except ImportError:
            logging.error("Не удалось импортировать BaseAgent из plugins.base_agent")
            continue

        # Ищем классы, унаследованные от BaseAgent
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            # Проверяем, что это класс, унаследованный от BaseAgent, но не сам BaseAgent
            if isinstance(attr, type) and issubclass(attr, BaseAgent) and attr is not BaseAgent:
                try:
                    agent_instance = attr(tools=agent_manager.tools)  # Передаем инструменты при инициализации
                    agent_manager.register_agent(agent_instance)
                    logging.info(f"Загружен агент: {attr_name}")
                except Exception as e:
                    logging.error(f"Не удалось инициализировать агента {attr_name}: {e}")

# --------------------- Загрузка Инструментов ---------------------
def load_tools() -> Dict[str, Any]:
    """
    Динамически загружает все инструменты из папки tools и возвращает словарь инструментов.
    """
    tools = {}
    sys.path.insert(0, TOOLS_FOLDER)  # Чтобы Python мог импортировать из папки tools

    for importer, module_name, ispkg in pkgutil.iter_modules([TOOLS_FOLDER]):
        # Пропускаем __init__
        if module_name == "__init__":
            continue

        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            logging.error(f"Не удалось импортировать инструмент {module_name}: {e}")
            continue

        # Предполагается, что каждый инструмент экспортирует объект с именем, совпадающим с именем модуля
        tool = getattr(module, module_name, None)
        if tool is None:
            # Проверим, есть ли другие объекты в модуле
            if hasattr(module, 'tool'):
                tool = getattr(module, 'tool')
            else:
                logging.error(f"Инструмент {module_name} не содержит объекта с именем {module_name} или 'tool'")
                continue

        tools[module_name] = tool
        logging.info(f"Загружен инструмент: {module_name}")

    return tools

# --------------------- Класс бота на aiogram ---------------------
class AITelegramBot:
    def __init__(self, token: str, tools: Dict[str, Any]):
        self.bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode="HTML")
        )
        self.dp = Dispatcher()

        # Добавляем объект бота в инструменты для использования агентами
        self.tools = tools
        self.tools['bot'] = self.bot  # Для агентов, которым нужен доступ к боту

        # Инициализируем менеджер агентов с доступными инструментами
        self.agent_manager = AgentManager(tools=tools)
        # Загружаем все агенты из папки plugins
        load_agents(self.agent_manager)

        # Получаем информацию о агентах для использования в системном сообщении
        agents_info = self.agent_manager.get_agents_info()

        # Системное сообщение для GPT, включая информацию о доступных агентах
        self.system_prompt = (
            "Ты — GPT-бот, способный общаться с пользователями и выполнять различные задачи с помощью агентов.\n\n"
            "Доступные агенты:\n" +
            "\n".join([f"/{agent['name']} — {agent['description']}" for agent in agents_info]) +
            "\n\n"
            "При необходимости используй агентов для выполнения задач. Ответь в формате JSON следующей структуры:\n"
            "{\n"
            '  "response": "Текст ответа GPT",\n'
            '  "agent_calls": [\n'
            '    {\n'
            '      "agent": "название_агента",\n'
            '      "args": "аргументы"\n'
            '    }\n'
            '  ]\n'
            "}\n\n"
            "Если не требуется вызывать агента, верни только поле 'response'."
        )

        # Регистрируем хендлер для сообщений
        @self.dp.message()
        async def message_handler(message: Message):
            user_text = message.text
            ai_response = await self.get_ai_response(user_text)
            final_response = ""

            try:
                response_data = json.loads(ai_response)
                final_response += response_data.get("response", "")
                agent_calls = response_data.get("agent_calls", [])

                for call in agent_calls:
                    agent_name = call.get("agent")
                    args = call.get("args", "")
                    agent = self.agent_manager.command_map.get(agent_name.lower())
                    if agent:
                        agent_response = await agent.handle(args, message)
                        final_response += f"\n\nАгент /{agent_name} ответил:\n{agent_response}"
                    else:
                        final_response += f"\n\nНеизвестный агент: /{agent_name}"
            except json.JSONDecodeError:
                # Если ответ не в формате JSON, просто отправляем как есть
                final_response = ai_response

            await message.answer(final_response)

    async def get_ai_response(self, user_message: str) -> str:
        """
        Отправляет запрос к GPT и получает ответ.
        """

        api_key = os.getenv("GPT_API_KEY")
    
        if not api_key:
            logging.error("GPT_API_KEY не установлена в переменных окружения.")
            return "Внутренняя ошибка: API ключ GPT не настроен."
        
        # Читаем базовый URL из GPT_BASE_URL (если не задан, используется дефолтный)
        base_url = os.getenv("GPT_BASE_URL", "https://api.openai.com/v1")

        # Читаем модель из переменной окружения; если не задана, используем дефолтную
        gpt_model = os.getenv("GPT_MODEL", "gpt-3.5-turbo")

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

        try:
            completion = await client.chat.completions.create(
                model=gpt_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=5000,
                temperature=0.7,
            )
            response_text = completion.choices[0].message.content
            return response_text
        except Exception as e:
            logging.error(f"Ошибка при обращении к GPT: {e}")
            return "Произошла ошибка при обработке вашего запроса."

    async def run(self):
        # Запускаем бота (long-polling)
        await self.dp.start_polling(self.bot)

# --------------------- Точка входа ---------------------
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Читаем токен бота из .env
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        logging.error("Переменная окружения TELEGRAM_BOT_TOKEN не установлена!")
        raise ValueError("Переменная окружения TELEGRAM_BOT_TOKEN не установлена!")

    # Загружаем инструменты
    tools = load_tools()

    bot_app = AITelegramBot(token=telegram_token, tools=tools)
    await bot_app.run()

if __name__ == "__main__":
    asyncio.run(main())
