from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from services.google_calendar import GoogleCalendarClient
from services.user_service import UserService
import os

load_dotenv()


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        if event.message:
            user_id = event.message.from_user.id
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
        else:
            return

        token_validity = await UserService.get_token(user_id=user_id, session=data.get("session"))

        if token_validity:
            return await handler(event, data)
        else:
            auth_url = GoogleCalendarClient().get_auth_url(
                redirect_uri=os.getenv("BASE_URL")+'/auth/callback',
                state=user_id
            )

            builder = InlineKeyboardBuilder()
            builder.button(text="Войти через гугл", url=auth_url)

            if event.message:
                await event.message.answer(
                    "Для продолжения работы дайте доступ к гугл календарю",
                    reply_markup=builder.as_markup()
                )
            elif event.callback_query:
                await event.callback_query.answer(
                    "Для продолжения работы дайте доступ к гугл календарю"
                )
                await event.callback_query.message.answer(
                    "Для продолжения работы дайте доступ к гугл календарю",
                    reply_markup=builder.as_markup()
                )
