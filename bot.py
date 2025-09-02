import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status

import config
from database.base import Base, async_session_factory, engine
from handlers import callback_handlers, message_handlers
from middlewares.auth_middleware import AuthMiddleware
from middlewares.db_middleware import DbSessionMiddleware
from middlewares.sheduler_middleware import SchedulerMiddleware
from services.google_calendar import GoogleCalendarClient
from services.user_service import UserService

load_dotenv()

async def create_tables():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logging.info("Tables created successfully")
    except Exception as e:
        logging.error(f"Error creating tables: {e}")
        raise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

BASE_URL = os.getenv('BASE_URL')
if not BASE_URL:
    raise ValueError("BASE_URL is not set in environment variables")

scheduler = AsyncIOScheduler()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.update.middleware(DbSessionMiddleware())
dp.update.middleware(SchedulerMiddleware(scheduler))
dp.update.middleware(AuthMiddleware())
dp.include_router(callback_handlers.callback_router)
dp.include_router(message_handlers.message_router)


@app.on_event("startup")
async def on_startup():
    try:
        scheduler.start()
        logger.info("Scheduler started successfully")

        await create_tables()
        webhook_url = f"{BASE_URL}/bot/update"
        await bot.set_webhook(url=webhook_url, allowed_updates=["message", "callback_query"])
        logger.info(f"Webhook set to {webhook_url}")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise


@app.post("/bot/update")
async def bot_webhook(request: Request):
    try:
        body = await request.body()
        update = Update.model_validate_json(body)
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
    return {"ok": True}


@app.get("/auth/callback")
async def oauth_callback(request: Request, state, code):
    user_id = state
    tokens = GoogleCalendarClient().exchange_code_for_tokens(code, redirect_uri=f'{BASE_URL}/auth/callback')
    refresh_token = tokens.get('refresh_token')
    validity = GoogleCalendarClient().check_token_validity(refresh_token)

    if validity:
        async with async_session_factory() as session:
            await UserService.save_token(user_id=user_id,
                                         refresh_token=refresh_token,
                                         session=session)
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(chat_id=user_id, text=config.success_auth_text, parse_mode='html')
        return {"ok": True}
    return {"error", 401}


@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()
    logger.info("Bot session closed")
