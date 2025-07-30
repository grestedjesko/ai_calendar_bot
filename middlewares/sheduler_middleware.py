from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class SchedulerMiddleware(BaseMiddleware):
    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler  # Инициализация с планировщиком

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        # Передаем планировщик в data
        data["scheduler"] = self.scheduler
        return await handler(event, data)
