import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from datetime import datetime

from database.models import EventModel

class EventRepository:
    """
    Класс для работы с базой данных и сохранения информации о событиях.
    """

    @staticmethod
    async def save_event(session: AsyncSession, user_id: int, summary: str, start: datetime, end: datetime, gcal_id: str):
        new_event = EventModel(
            user_id=user_id,
            summary=summary,
            start=start,
            end=end,
            gcal_id=gcal_id
        )
        session.add(new_event)
        await session.commit()
        return new_event.id

    @staticmethod
    async def get_event(session: AsyncSession, event_id: int, user_id: int):
        stmt = sa.select(EventModel).where(EventModel.id == event_id, EventModel.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_event(session: AsyncSession, event_id: int, new_end: datetime):
        stmt = sa.select(EventModel).where(EventModel.id == event_id)
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()
        event.end = new_end
        session.add(event)
        await session.commit()
        return event

    @staticmethod
    async def delete_event(session: AsyncSession, event_id: int):
        stmt = sa.delete(EventModel).where(EventModel.id == event_id)
        await session.execute(stmt)
        await session.commit()
