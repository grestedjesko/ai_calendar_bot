import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (AsyncAttrs, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm import DeclarativeBase

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

DATABASE_NAME = os.getenv("DATABASE_NAME")

DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_NAME}.db"

engine = create_async_engine(DATABASE_URL,
                             echo=False,
                             pool_pre_ping=True,
                             pool_recycle=3600,
                             connect_args={"check_same_thread": False}
                             )

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(AsyncAttrs, DeclarativeBase):
    pass

