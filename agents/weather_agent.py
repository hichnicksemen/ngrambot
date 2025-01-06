# agents/weather_agent.py

import os
import logging
from agents.base_agent import BaseAgent
from aiogram.types import Message
from typing import Dict, Any

class WeatherAgent(BaseAgent):
    """
    Агент для обработки команды /weather и предоставления информации о погоде.
    """

    def __init__(self, tools: Dict[str, Any]):
        super().__init__(tools)
        self.api_key = os.getenv("WEATHER_API_KEY")
        if not self.api_key:
            logging.error("Переменная окружения WEATHER_API_KEY не установлена!")
            raise ValueError("Переменная окружения WEATHER_API_KEY не установлена!")

    def get_name(self) -> str:
        return "weather"

    def get_description(self) -> str:
        return "Предоставляет информацию о текущей погоде в указанном городе. Пример использования: /weather Москва"

    async def handle(self, args: str, message: Message) -> str:
        if not args:
            return "Пожалуйста, укажите город. Пример: /weather Москва"

        city = args.strip()
        try:
            weather_info = await self.get_weather(city)
            return weather_info
        except Exception as e:
            return f"Произошла ошибка при получении погоды: {e}"

    async def get_weather(self, city: str) -> str:
        """
        Получает текущую погоду для указанного города через OpenWeatherMap API.
        Использует HTTPClient из инструментов.
        """
        http_client = self.tools.get('http_client')
        if not http_client:
            return "Внутренняя ошибка: HTTP клиент не доступен."

        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric',
            'lang': 'ru'
        }

        try:
            data = await http_client.get(url, params=params)
            description = data['weather'][0]['description'].capitalize()
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            return f"Погода в {city}:\n{description}\nТемпература: {temp}°C\nВлажность: {humidity}%\nСкорость ветра: {wind_speed} м/с"
        except Exception as e:
            return f"Не удалось получить данные о погоде: {e}"
