import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.google_calendar import GoogleCalendarClient


class UserService:
    """Класс для работы с данными пользователя"""

    @staticmethod
    async def get_token(user_id: int, session: AsyncSession):
        """
        Получает refresh_token пользователя и проверяет его валидность.
        Если токен валиден, возвращает его, иначе False.

        Args:
            user_id (int): Идентификатор пользователя.
            session (AsyncSession): Сессия для работы с базой данных.

        Returns:
            str | bool: Токен или False, если токен не валиден.
        """
        stmt = sa.select(User.refresh_token).where(User.tg_id == user_id)
        result = await session.execute(stmt)
        token = result.scalar_one_or_none()

        if token:
            validity = GoogleCalendarClient().check_token_validity(token)
            if validity:
                 return token
            return validity
        return False

    @staticmethod
    async def save_token(user_id: int, refresh_token: str, session: AsyncSession):
        """
        Сохраняет или обновляет refresh_token пользователя в базе данных.
        Если токен уже существует, обновляет его, если нет - вставляет новый.

        Args:
            user_id (int): Идентификатор пользователя.
            refresh_token (str): Новый refresh_token для пользователя.
            session (AsyncSession): Сессия для работы с базой данных.

        Returns:
            bool: True, если токен успешно сохранен или обновлен, иначе False.
        """
        if refresh_token:
            stmt = sa.select(User).where(User.tg_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                stmt = sa.update(User).where(User.tg_id == user_id).values(refresh_token=refresh_token)
                await session.execute(stmt)
            else:
                stmt = sa.insert(User).values(tg_id=user_id, refresh_token=refresh_token)
                await session.execute(stmt)

            await session.commit()
            return True
        return False