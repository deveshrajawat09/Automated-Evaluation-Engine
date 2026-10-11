from __future__ import annotations

import json
from datetime import datetime
from os import getenv
from pathlib import Path
from typing import Any

from sqlalchemy import JSON, DateTime, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class StateRecord(Base):
    __tablename__ = "hackeval_state"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


def _database_url() -> str:
    return getenv("DATABASE_URL", "sqlite:///./hackeval-local.db").replace("postgres://", "postgresql+psycopg://", 1)


engine = create_engine(_database_url(), pool_pre_ping=True)


def init_database() -> None:
    Base.metadata.create_all(engine)


def load_state() -> dict[str, Any] | None:
    init_database()
    with Session(engine) as session:
        record = session.scalar(select(StateRecord).where(StateRecord.key == "store"))
        return record.value if record else None


def save_state(state: dict[str, Any]) -> None:
    init_database()
    with Session(engine) as session:
        record = session.get(StateRecord, "store")
        if record is None:
            record = StateRecord(key="store", value=state)
            session.add(record)
        else:
            record.value = state
            record.updated_at = datetime.utcnow()
        session.commit()
