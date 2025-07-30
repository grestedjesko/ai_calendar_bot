from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update

from database.base import async_session_factory


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        async with async_session_factory() as session:
            data["session"] = session  # Передаём сессию в data
            return await handler(event, data)
