from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    refresh_token: Mapped[str] = mapped_column(String(255))  # Added length (255 is common for tokens)

    events: Mapped[list["EventModel"]] = relationship(back_populates="user")


class EventModel(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    summary: Mapped[str] = mapped_column(String(255))  # Added length
    start: Mapped[datetime] = mapped_column(DateTime)
    end: Mapped[datetime] = mapped_column(DateTime)
    gcal_id: Mapped[str] = mapped_column(String(255))  # Added length
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User] = relationship(back_populates="events")
    scheduled_event: Mapped["ScheduledEvent"] = relationship("ScheduledEvent", uselist=False, back_populates="event")


class ScheduledEvent(Base):
    __tablename__ = "scheduled_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    job_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reminder_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    event: Mapped[EventModel] = relationship("EventModel", back_populates="scheduled_event")