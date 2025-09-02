from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from services.user_service import UserService
from services.google_calendar import GoogleCalendarClient
from aiogram import Bot
import pytz
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from database.models import EventModel
from services.utils import format_duration
from typing import Iterable


class ReminderService:
    """
    Класс для управления напоминаниями.
    """

    def __init__(self, scheduler: AsyncIOScheduler, bot: Bot, session: AsyncSession):
        self.scheduler = scheduler
        self.bot = bot
        self.session = session

    async def schedule_reminders(self,
                                 event_id: int,
                                 start: datetime,
                                 before_start: Iterable[int],
                                 after_now: Iterable[int],
                                 user_id: int):
        """
        Планирует напоминания для события.
        """
        scheduled = []
        tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(tz)

        # ДО начала события
        for m in sorted(set(int(x) for x in before_start if int(x) >= 0)):
            run_at = start - timedelta(minutes=m)
            if run_at > now:
                job = self.scheduler.add_job(
                    self.send_reminder,
                    DateTrigger(run_date=run_at),
                    args=[event_id, f"за {m} мин. до начала", user_id]  # <— передаём ярлык
                )
                scheduled.append(job)

        # ОТ сейчас
        for m in sorted(set(int(x) for x in after_now if int(x) >= 0)):
            run_at = now + timedelta(minutes=m)
            job = self.scheduler.add_job(
                self.send_reminder,
                DateTrigger(run_date=run_at),
                args=[event_id, f"через {m} мин.", user_id]  # <— передаём ярлык
            )
            scheduled.append(job)

        return scheduled


    async def send_reminder(self, event_id: int, minutes_left: int, user_id: int):
        """
        Отправляет напоминание пользователю.
        """
        result = await self.session.execute(
            sa.select(EventModel).where(EventModel.id == event_id, EventModel.user_id == user_id))
        event = result.scalar_one_or_none()

        if not event or not event.is_active:
            return

        token = await UserService.get_token(user_id=user_id, session=self.session)
        google_event = GoogleCalendarClient().get_event(refresh_token=token, event_id=event.gcal_id)

        if not google_event:
            return

        event_start_time = datetime.strftime(event.start, "%H:%M")
        event_start_date = datetime.strftime(event.start, "%d.%m.%Y")

        event_end_time = datetime.strftime(event.end, "%H:%M")

        duration_str = format_duration((event.end - event.start).minutes)

        message = f"""<b>🔔 {event.summary}</b> 

<blockquote>
{event_start_date}
С {event_start_time} до {event_end_time}
Продолжительность: ⌛️ <b>{duration_str}</b></blockquote>
"""

        await self.bot.send_message(chat_id=user_id, text=message, parse_mode='html')
