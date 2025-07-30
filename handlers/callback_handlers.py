from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from services.event_service import Event
from states import EventStates

callback_router = Router()


@callback_router.callback_query(F.data.startswith("cancel_event_id="))
async def cancel_event(call: CallbackQuery, session: AsyncSession, scheduler: AsyncIOScheduler):
    event_id = call.data.replace("cancel_event_id=", "")
    await Event.cancel(user_id=call.from_user.id, event_id=event_id, session=session)
    await call.message.edit_text('Событие отменено')


@callback_router.callback_query(F.data.startswith("edit_duration_event_id="))
async def edit_duration_event(call: CallbackQuery, state: FSMContext):
    event_id = call.data.replace("edit_duration_event_id=", "")

    await call.message.answer('Введите новую продолжительность в минутах')

    await state.update_data(event_id=event_id)
    await state.set_state(EventStates.duration)