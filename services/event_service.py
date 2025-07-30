from datetime import datetime, timedelta
from services.google_calendar import GoogleCalendarClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.reminder_service import ReminderService
from services.event_repository import EventRepository
from services.user_service import UserService
import pytz
from sqlalchemy.ext.asyncio.session import AsyncSession
from aiogram import Bot

class Event:
    """
    Класс для создания и управления событием.
    """

    def __init__(self, user_id: int, summary: str, start: datetime, end: datetime, session: AsyncSession,
                 scheduler: AsyncIOScheduler, bot: Bot):
        self.user_id = user_id
        self.summary = summary
        self.start = start

        timezone = pytz.timezone('Europe/Moscow')
        start_dt = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
        self.start = timezone.localize(start_dt)
        end_dt = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S')
        self.end = timezone.localize(end_dt)

        self.session = session
        self.scheduler = scheduler
        self.bot = bot

        self.google_calendar_service = GoogleCalendarClient()
        self.event_repository = EventRepository()
        self.reminder_service = ReminderService(scheduler, bot, session)

    async def create(self) -> tuple[int, str]:
        """
        Создает новое событие, сохраняет его в базе данных и планирует напоминания.
        """

        # Создание события в Google Calendar
        token = await UserService.get_token(user_id=self.user_id, session=self.session)
        google_event = self.google_calendar_service.create_event(token, self.summary, self.start, self.end)
        gcal_id = google_event.get('id')
        link = google_event.get('htmlLink')

        # Сохранение события в базу данных
        event_id = await self.event_repository.save_event(self.session, self.user_id,
                                                          self.summary, self.start,
                                                          self.end, gcal_id)

        # Планирование напоминаний
        await self.reminder_service.schedule_reminders(event_id, self.start, reminder_times=[30, 5, 0], user_id=self.user_id)

        return event_id, link

    @staticmethod
    async def cancel(user_id: int, event_id: int, session: AsyncSession):
        """
        Отменяет событие и удаляет связанные с ним напоминания.
        """
        base_event = await EventRepository.get_event(session, event_id, user_id)
        if base_event:
            token = await UserService.get_token(user_id=user_id, session=session)
            GoogleCalendarClient().delete_event(refresh_token=token,
                                                event_id=base_event.gcal_id)
            base_event.is_active = False
            await session.commit()

            # Удаление напоминаний
            await EventRepository.delete_event(session, event_id)
            return True
        return False

    @staticmethod
    async def update_duration(duration: int, user_id: int, event_id: int, session: AsyncSession):
        """
        Обновляет продолжительность события.
        """
        base_event = await EventRepository.get_event(session, event_id, user_id)
        if base_event:
            base_event.end = base_event.start + timedelta(minutes=duration)
            token = await UserService.get_token(user_id=user_id, session=session)

            timezone = pytz.timezone('Europe/Moscow')
            end_dt = timezone.localize(base_event.end)

            GoogleCalendarClient().update_event(refresh_token=token,
                                                event_id=base_event.gcal_id,
                                                end=end_dt)
            await session.commit()
            return base_event.end
        return None
