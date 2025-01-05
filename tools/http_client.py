# tools/http_client.py

import aiohttp
import asyncio
from typing import Any, Dict, Optional

class HTTPClient:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def post(self, url: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()

    async def close(self):
        await self.session.close()

# Создаем экземпляр HTTPClient
http_client = HTTPClient()

# Асинхронная функция для корректного закрытия сессии при завершении программы
async def shutdown_http_client():
    await http_client.close()
