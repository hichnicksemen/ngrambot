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
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            "Ты — GPT-бот, который не только объясняет свои действия, но и полностью выполняет поставленные задачи. "
            "Используй ReAct подход (Reasoning + Acting) для решения задач.\n\n"
            "Правила работы с агентами:\n"
            "1. Сначала планируй полный набор действий\n"
            "2. Выполняй ВСЕ запланированные действия через agent_calls\n"
            "3. Анализируй результаты КАЖДОГО действия\n"
            "4. Продолжай выполнение, пока задача не будет полностью решена\n"
            "5. Формируй итоговый ответ на основе ВСЕХ полученных результатов\n\n"
            "При ответе строго следуй формату:\n"
            "Thought: детальное планирование всех необходимых действий\n"
            "Action: вызов первого агента\n"
            "Observation: анализ результата\n"
            "Thought: планирование следующего действия\n"
            "Action: вызов следующего агента\n"
            "Observation: анализ результата\n"
            "... (повторяй для каждого необходимого действия)\n"
            "Final Response: полный ответ, объединяющий все результаты\n\n"
            f"Доступные агенты:\n" +
            "\n".join([f"{agent['name']} — {agent['description']}" for agent in agents_info]) +
            "\n\n"
            "Пример правильного ответа в JSON:\n"
            "{\n"
            '  "reasoning": "Thought: Нужно узнать погоду и время\\n'\
            'Action: Вызываю weather для погоды\\n'\
            'Observation: Получены данные о погоде\\n'\
            'Action: Обрабатываю время\\n'\
            'Final Response: Объединяю информацию",\n'
            '  "response": "Сейчас [время] и [погода]",\n'
            '  "agent_calls": [\n'
            '    {"agent": "weather", "args": "Moscow"},\n'
            '    {"agent": "time", "args": "+2 hours"}\n'
            "  ]\n"
            "}\n\n"
            "ВАЖНО:\n"
            "1. ВСЕГДА выполняй действия через agent_calls\n"
            "2. Не просто планируй, а реально ВЫЗЫВАЙ агентов\n"
            "3. Используй все необходимые агенты для полного решения задачи\n"
            "4. Объединяй результаты всех агентов в финальном ответе"
        )

        @self.dp.message()
        async def message_handler(message: Message):
            if not message.text:
                return

            if message.text.startswith('/'):
                # Remove leading slash and split command
                command_full = message.text[1:].split(maxsplit=1)
                command_parts = command_full[0].split('_')  # Split by underscore for subcommands
                base_command = command_parts[0].lower()  # Get base command (e.g., 'memory' from 'memory_get')
                
                # Prepare args: if there's a subcommand, add it to the beginning of args
                args = ""
                if len(command_parts) > 1:
                    args = command_parts[1]  # Add subcommand to args
                    if len(command_full) > 1:
                        args += " " + command_full[1]
                elif len(command_full) > 1:
                    args = command_full[1]
                
                # Try to find and execute the base command
                agent = self.agent_manager.command_map.get(base_command)
                if agent:
                    agent_response = await agent.handle(args, message)
                    await message.answer(agent_response)
                    return
                else:
                    await message.answer(f"Неизвестная команда: /{base_command}")
                    return

            # Запускаем цикл ReAct
            final_response = await self.execute_react_cycle(message.text, message)
            await message.answer(final_response)

    async def execute_react_cycle(
        self,
        user_message: str,
        message,
        context: Dict[str, Any] = None,
        iteration_count: int = 0,
        max_iterations: int = 5
    ) -> str:
        if context is None:
            context = {}

        if iteration_count >= max_iterations:
            logger.warning("Достигнут лимит итераций для ReAct цикла!")
            context["error"] = "Достигнут лимит итераций"
            return await self.get_final_response(user_message, context)

        calls_history = context.setdefault("calls_history", [])
        progress_history = context.setdefault("progress_history", [])
        
        logger.debug(f"===== ИТЕРАЦИЯ #{iteration_count} =====")
        logger.debug(f"Текущий контекст:\n{context}")

        # Формируем сообщение для модели с контекстом и прогрессом
        full_message = self.format_message_with_context(user_message, context)
        ai_response = await self.get_ai_response(full_message)

        try:
            response_data = json.loads(ai_response)
        except json.JSONDecodeError as e:
            context["error"] = f"Ошибка парсинга JSON: {str(e)}"
            return await self.execute_react_cycle(user_message, message, context, iteration_count + 1)

        # Получаем текущие вызовы агентов
        agent_calls = response_data.get("agent_calls", [])
        calls_history.append(agent_calls)

        # Выполняем вызовы агентов и собираем результаты
        agent_results = await self.execute_agent_calls(agent_calls, message)
        
        # Анализируем прогресс
        progress = self.analyze_progress(context, agent_results, response_data)
        progress_history.append(progress)

        # Обновляем контекст результатами
        context.update(agent_results)

        # Если все агенты выполнились успешно, формируем финальный ответ
        if progress.get("success", False):
            final_response = []
            
            # Добавляем рассуждения
            if "reasoning" in response_data:
                reasoning = response_data["reasoning"].replace(
                    "Thought:", "💭 Размышление:"
                ).replace(
                    "Action:", "⚡️ Действие:"
                ).replace(
                    "Observation:", "👁 Наблюдение:"
                ).replace(
                    "Final Response:", "✅ Итоговый ответ:"
                )
                final_response.append("🤖 Процесс решения:\n" + reasoning)

            # Добавляем результаты агентов
            if "response" in response_data:
                response_text = response_data["response"]
                # Заменяем плейсхолдеры результатами агентов
                for agent_name, result in progress.get("results", {}).items():
                    if not isinstance(result, str) or result.startswith("❌"):
                        continue
                    placeholder = f"[{agent_name}]"
                    if placeholder in response_text:
                        response_text = response_text.replace(placeholder, result)
                final_response.append("\n🎯 Итоговый результат: " + response_text)
            else:
                # Если нет response в JSON, формируем из результатов агентов
                results = [result for result in agent_results.values() 
                          if isinstance(result, str) and not result.startswith("❌")]
                if results:
                    final_response.append("\n🎯 Полученные результаты:\n" + "\n".join(results))

            # Возвращаем полный ответ
            return "\n".join(final_response)

        # Если есть ошибки или не все агенты выполнились, продолжаем цикл
        if agent_results or "error" in context:
            return await self.execute_react_cycle(user_message, message, context, iteration_count + 1)

        return self.format_final_response(response_data)

    async def execute_agent_calls(self, agent_calls: List[Dict[str, str]], message: Message) -> Dict[str, str]:
        """
        Выполняет вызовы агентов и возвращает словарь с результатами.
        """
        results = {}
        for call in agent_calls:
            agent_name = call.get("agent", "").lower().lstrip("/")
            args = call.get("args", "").lstrip("/")

            # Если это повторный вызов того же агента с теми же аргументами, пропускаем
            call_key = f"{agent_name}:{args}"
            if call_key in results:
                logger.info(f"Пропускаем дублирующий вызов: {call_key}")
                continue

            agent = self.agent_manager.command_map.get(agent_name)
            if agent:
                try:
                    logger.info(f"Вызов агента '{agent_name}' с аргументами: {args}")
                    result = await agent.handle(args, message)
                    results[agent_name] = result  # Сохраняем по имени агента
                    logger.info(f"Агент '{agent_name}' вернул результат: {result}")
                except Exception as e:
                    error_msg = f"Ошибка при вызове агента {agent_name}: {str(e)}"
                    logger.error(error_msg)
                    results[f"{agent_name}_error"] = error_msg
            else:
                logger.error(f"Агент '{agent_name}' не найден")
                results[f"{agent_name}_error"] = f"Агент '{agent_name}' не найден"

        return results

    def analyze_progress(self, context: Dict[str, Any], new_results: Dict[str, Any], response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализирует прогресс в решении задачи"""
        # Подсчитываем успешные и неуспешные вызовы
        successful_calls = sum(1 for result in new_results.values() 
                             if isinstance(result, str) and not result.startswith("❌"))
        failed_calls = sum(1 for result in new_results.values() 
                         if isinstance(result, str) and result.startswith("❌"))
        
        # Проверяем успешность выполнения всей задачи
        all_calls_processed = len(response_data.get("agent_calls", [])) == len(new_results)
        success = successful_calls > 0 and failed_calls == 0 and all_calls_processed

        return {
            "has_new_info": bool(new_results),
            "error_resolved": "error" in context and "error" not in new_results,
            "reasoning_changed": self.has_reasoning_changed(context, response_data),
            "agent_calls_count": len(response_data.get("agent_calls", [])),
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success": success,
            "results": new_results  # Сохраняем результаты для использования в финальном ответе
        }

    def is_stuck(self, progress_history: List[Dict[str, Any]]) -> bool:
        """
        Определяет, застряло ли выполнение, анализируя историю прогресса
        """
        if len(progress_history) < 3:
            return False

        last_three = progress_history[-3:]
        
        # Проверяем наличие новой информации
        no_new_info = not any(p["has_new_info"] for p in last_three)
        
        # Проверяем изменения в рассуждениях
        no_reasoning_changes = not any(p["reasoning_changed"] for p in last_three)
        
        # Проверяем количество вызовов агентов
        same_calls_count = all(p["agent_calls_count"] == last_three[0]["agent_calls_count"] 
                             for p in last_three)

        return no_new_info and no_reasoning_changes and same_calls_count

    def has_reasoning_changed(self, context: Dict[str, Any], new_response: Dict[str, Any]) -> bool:
        """
        Проверяет, изменились ли рассуждения LLM по сравнению с предыдущей итерацией
        """
        if "last_reasoning" not in context:
            context["last_reasoning"] = new_response.get("reasoning", "")
            return True

        old_reasoning = context["last_reasoning"]
        new_reasoning = new_response.get("reasoning", "")
        context["last_reasoning"] = new_reasoning

        # Простое сравнение на неравенство
        return old_reasoning != new_reasoning

    async def get_final_response(self, user_message: str, context: Dict[str, Any]) -> str:
        """
        Запрашивает у LLM финальный ответ с учетом всего контекста
        """
        full_context = json.dumps(context, ensure_ascii=False, indent=2)
        final_prompt = (
            f"Задача: {user_message}\n\n"
            f"Контекст выполнения:\n{full_context}\n\n"
            "Пожалуйста, сформируй финальный ответ, учитывая все полученные результаты и ошибки."
        )
        return await self.get_ai_response(final_prompt)

    def format_message_with_context(self, user_message: str, context: Dict[str, Any]) -> str:
        """
        Форматирует сообщение для LLM с учетом контекста
        """
        message_parts = [user_message]

        filtered_context = {k: v for k, v in context.items() 
                          if k not in ["calls_history", "progress_history", "last_reasoning"]}
        
        if (filtered_context):
            message_parts.append("\nПредыдущие результаты:")
            for agent_name, result in filtered_context.items():
                if agent_name != "error":
                    message_parts.append(f"\nРезультат от {agent_name}:\n{result}")

        if "error" in context:
            message_parts.append(f"\nПредыдущая ошибка:\n{context['error']}")

        return "\n".join(message_parts)

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

    def format_final_response(self, response_data: Dict[str, Any]) -> str:
        """Форматирует финальный ответ из данных ответа GPT."""
        if isinstance(response_data, str):
            return response_data

        if isinstance(response_data, dict):
            parts = []
            
            # Добавляем рассуждения
            if "reasoning" in response_data:
                reasoning = response_data["reasoning"]
                if not any(marker in reasoning for marker in ["Observation:", "Action:", "Final Response:"]):
                    return "❌ Требуется выполнение действий через агентов"
                
                formatted_reasoning = (
                    reasoning
                    .replace("Thought:", "💭 Размышление:")
                    .replace("Action:", "⚡️ Действие:")
                    .replace("Observation:", "👁 Наблюдение:")
                    .replace("Final Response:", "✅ Итоговый ответ:")
                )
                parts.append("🤖 Процесс решения:\n" + formatted_reasoning)
            
            # Проверяем наличие вызовов агентов
            if not response_data.get("agent_calls"):
                return "❌ Отсутствуют вызовы агентов для выполнения задачи"
            
            # Добавляем финальный ответ
            if "response" in response_data:
                parts.append("\n🎯 Результат: " + response_data["response"])
            
            return "\n".join(parts)

        return "Произошла ошибка при обработке ответа."

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
