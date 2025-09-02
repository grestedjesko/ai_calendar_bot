from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from services import utils
from services.ai_service import AiService
from services.event_service import Event
from states import EventStates
from services.utils import join_humanized

message_router = Router()


@message_router.message(Command('start'))
async def start(message: types.Message):
    await message.answer('''Привет! Я помогу тебе быстро запланировать событие в календаре. 🗓

Просто назови событие и его время — остальное я сделаю за тебя.

Если не уточнишь дату — я автоматически выберу ближайшее время.
Также можешь не указывать продолжительность — я сам решу, сколько времени нужно для события (но учти, что могу ошибиться).''')


@message_router.message(StateFilter(EventStates.duration))
async def edit_duration(message: types.Message, state: FSMContext, session: AsyncSession):
    print(message.text)
    if not message.text.isdigit():
        await message.answer('Ошибка. Введите новую продолжительность в минутах')
        return

    duration = int(message.text)
    data = await state.get_data()
    event_id = data.get('event_id')

    end = await Event.update_duration(duration=duration, user_id=message.from_user.id, event_id=event_id, session=session)
    end_datetime = datetime.strftime(end, "%d.%m.%Y %H:%M")
    await message.answer(f'Время окончания события изменено на {end_datetime}')
    await state.clear()


@message_router.message()
async def answer_chat(message: types.Message, session: AsyncSession, scheduler: AsyncIOScheduler):
    msg = await message.answer('🧠 Анализирую задачу')
    try:
        details = AiService().get_task_details_from_openai(message.text)
        if not details:
            await msg.edit_text('Я не нашел в сообщении всех деталей о событии. Попробуй еще раз.')
            return
    except Exception as e:
        print(e)
        await msg.edit_text('Я не нашел в сообщении всех деталей о событии. Попробуй еще раз.')
        return

    event = Event(user_id=message.from_user.id,
                  summary=details.get('summary'),
                  start=details.get('start'),
                  end=details.get('end'),
                  reminders=details.get('reminders'),
                  session=session,
                  scheduler=scheduler,
                  bot=message.bot)
    event_id, link = await event.create()

    kbd = InlineKeyboardBuilder()
    kbd.add(InlineKeyboardButton(text='👀 Посмотреть', url=link))
    kbd.add(InlineKeyboardButton(text='⌛️ Изменить продолжительность', callback_data=f'edit_duration_event_id={event_id}'))
    kbd.add(InlineKeyboardButton(text='🚫 Отменить', callback_data=f'cancel_event_id={event_id}'))
    kbd.adjust(1)

    event_start_date = datetime.strftime(event.start, "%d.%m.%Y")
    event_start_time = datetime.strftime(event.start, "%H:%M")
    event_end_date = datetime.strftime(event.end, "%d.%m.%Y")

    event_end_time = datetime.strftime(event.end, "%H:%M")
    event_summary = event.summary[0].upper() + event.summary[1:]
    duration = utils.format_duration(duration=details.get('duration'))

    if event.start.date() != event.end.date():
        duration_string = f'С {event_start_time} до {event_end_time} ({event_end_date})'
    else:
        duration_string = f'С {event_start_time} до {event_end_time}'

    reminders_obj = details.get('reminders') or {}
    before = reminders_obj.get('before_start') or [30, 5, 0]
    after = reminders_obj.get('after_now') or []

    before_text = join_humanized(before)
    after_text = join_humanized(after)

    if before and after:
        remind_text = f"🧠 Напомню: через {after_text}, а также за {before_text} до начала."
    elif after:
        remind_text = f"🧠 Напомню через {after_text}."
    else:
        remind_text = f"🧠 Напомню за {before_text} до начала."

    message_text = f'''🗓 Запланировал новое событие на {event_start_date}:

<blockquote><b>{event_summary}</b> 

{duration_string}
Продолжительность: ⌛️ <b>{duration}</b></blockquote>

🧠 Напомню {remind_text}.'''

    await msg.edit_text(message_text, reply_markup=kbd.as_markup(), parse_mode='HTML')
