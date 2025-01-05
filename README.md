# NGRAMBOT

**NGRAMBOT** — это универсальный Telegram-бот, легко расширяемый с помощью агентов и инструментов.
Бот написан на aiogram3 и позволяет добавлять новые функции (например, поиск, управление задачами, интеграции с внешними сервисами, покупка билетов и многое другое) путём создания модулей-агентов в папке agents.
Кроме того, бот поддерживает систему инструментов (tools), которые динамически загружаются и доступны всем агентам.

---

## Возможности

- **Подключение новых агентов и инструментов** без изменения ядра бота.
- **Динамическая загрузка агентов** из папки `agents`.
- **Поддержка инструментов (tools)** — общие модули для HTTP-запросов, БД, логгирования, планировщиков и т.д., доступные всем агентам.
- **AI ядро (GPT)**, принимающее решения о вызове агентов автоматически.
- **Управление выбором GPT-модели и базового URL** через переменные окружения (например, GPT_MODEL и GPT_BASE_URL).
- **Асинхронная обработка** сообщений на базе `aiogram3`.
- **Простое добавление любых интеграций** (например, ChatGPT, OpenWeatherMap, и т.д.).

---

## Установка

1. **Клонируйте репозиторий**:
   ```
   bash
   git clone https://github.com/hichnicksemen/ngrambot.git
   cd ngrambot
   ```

2. **Установите зависимости**:
    ```
    pip install -r requirements.txt
    ```

3. **Создайте и заполните переменные окружения (опционально)**:
Вы можете использовать файл .env (рекомендуется) или передавать переменные окружения напрямую. Ниже пример содержимого .env:
    ```
    TELEGRAM_BOT_TOKEN="1234567:EXAMPLE_TOKEN_ABCDEFG"
    OPENAI_API_KEY="ВАШ_OPENAI_КЛЮЧ"
    GPT_BASE_URL="https://example.com/v1"      # (необязательно) URL стороннего GPT-сервиса или прокси
    GPT_MODEL="gpt-3.5-turbo"                 # (необязательно) Модель по умолчанию
    ```
В зависимости от ваших нужд можно добавить любые другие переменные (например, ключи от внешних API).

## Запуск
Для запуска бота (Python 3.9+):
```python main.py```

После этого бот начнёт опрашивать Telegram в режиме long polling.
Убедитесь, что вы вставили ваш реальный токен Telegram-бота в код (или передали его через переменную окружения).

## Структура проекта
```
ngrambot/
├── main.py                # Точка входа: запуск бота
├── agents/               # Папка с плагинами (агентами)
│   ├── __init__.py
│   ├── base_agent.py      # Базовый класс агента
│   ├── search_agent.py    # Пример агента "поиск"
│   ├── tasks_agent.py     # Пример агента "список задач"
│   └── my_new_agent.py    # Другие агенты, которые вы добавите
├── tools/                 # Папка с инструментами
│   ├── __init__.py
│   ├── http_client.py     # Пример: HTTP-клиент
│   ├── logger.py          # Пример: настроенный логгер
│   ├── database.py        # Пример: класс для работы с БД
│   └── scheduler.py       # Пример: планировщик задач
├── requirements.txt       # Зависимости проекта
└── README.md              # Описание (вы читаете этот файл)
```

- main.py — содержит основную логику бота:

    - Загружает инструменты из папки tools (http_client, logger, database, scheduler и т.д.).
    - Создаёт AI ядро (GPT), управляющее сообщениями и при необходимости вызывающее агентов.
    - Инициализирует менеджер агентов (AgentManager), который сканирует папку plugins и регистрирует всех наследников BaseAgent.
    - Запускает бота (long polling).

- agents/ — папка, где лежат все агенты (плагины). Каждый агент — отдельный .py файл с классом, унаследованным от BaseAgent.

    - base_agent.py — базовый класс агента: описывает интерфейс (методы get_name, get_description, handle).
    - search_agent.py, tasks_agent.py — примеры агентов.
    - my_new_agent.py — любой новый агент, который вы добавляете.

- tools/ — папка, где лежат инструменты. Любой .py файл с экспортируемым объектом.

    - http_client.py — пример HTTP-клиента (на базе aiohttp).
    - logger.py — пример настроенного логгера.
    - database.py — пример класса для работы с SQLite.
    - scheduler.py — пример планировщика (apscheduler).

- requirements.txt — список зависимостей (aiogram, python-dotenv, openai и т.д.).

## Как добавить новый плагин

1. Создайте в папке agents новый файл, например my_new_agent.py

2. Подключите базовый класс:
```
from agents.base_agent import BaseAgent
from aiogram.types import Message
```

3. Создайте класс, унаследованный от BaseAgent, и переопределите требуемые методы:

```
class MyNewAgent(BaseAgent):
    def get_name(self) -> str:
        return "hello"

    def get_description(self) -> str:
        return "Отправляет приветственное сообщение"

    async def handle(self, args: str, message: Message) -> str:
        # Логика вашего агента
        if not args:
            return "Привет! Я новый агент!"
        return f"Привет! Ваши аргументы: {args}"

```

4. Перезапустите бота. Ваш агент будет автоматически обнаружен и зарегистрирован в AgentManager.

## Как добавить новый инструмент (tools)
1. Создайте новый файл в папке tools, например file_client.py.

2. Определите нужный класс или объект:
```
class FileClient:
    def __init__(self, base_path="files"):
        # ... инициализация ...
        pass

    def save_file(self, filename: str, content: bytes) -> str:
        # ... логика сохранения ...

# Экспортируем объект с именем, совпадающим с именем файла (file_client)
file_client = FileClient()
```
3. Использование:
    - В коде агента получите доступ к нему через self.tools['file_client'].
    - Пример: file_path = self.tools['file_client'].save_file("test.txt", b"hello").

Инструмент автоматически загрузится при старте бота и будет доступен всем агентам без дополнительных правок в main.py.

## Использование бота
**Шаги взаимодействия:**
1. Пользователь отправляет любое сообщение боту в Telegram.
2. Главное ядро (GPT) анализирует текст, формирует ответ:

    - Либо простой текст в response,
    - Либо текст + список вызовов агентов в agent_calls (формат JSON).

3. Бот получает JSON-ответ от GPT, при необходимости вызывает соответствующих агентов (например, weather, translate, reminder) и добавляет ответы этих агентов к финальному сообщению пользователю.

**Пример:**
```
Пользователь: "Переведи 'Привет мир' на испанский."
GPT: {
  "response": "Хорошо, перевожу...",
  "agent_calls": [
    {
      "agent": "translate",
      "args": "es Привет мир"
    }
  ]
}
Бот -> Агент translate -> "Hola mundo"
Бот: "Хорошо, перевожу...

Агент /translate ответил:
Hola mundo"
```

## Добавление/замена GPT-модели и базового URL
- Выбор модели задаётся переменной окружения GPT_MODEL (например, gpt-3.5-turbo, gpt-4, text-davinci-003 и т.д.).
- Изменение базового URL (например, если используете прокси или нестандартное API) задаётся через GPT_BASE_URL. По умолчанию используется https://api.openai.com/v1.
- В России можно использовать популярный сервис для доступа к GPT по API [vsegpt.ru](https://vsegpt.ru/?cmpad=p641059572)

## Лицензия
Проект распространяется под MIT License.

## Контакты
Если у вас есть вопросы или предложения, создайте issue или отправьте Pull Request.
Буду рад вашим идеям и новым плагинам!

[Телеграм для связи](https://t.me/Hichnick)