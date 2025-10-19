from __future__ import annotations

from collections.abc import AsyncGenerator

from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, create_engine

from app.config import get_settings
from app.models import app_metadata

settings = get_settings()

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite+aiosqlite"):
    db_url = db_url.replace("sqlite+aiosqlite", "sqlite", 1)

engine = create_engine(
    db_url,
    echo=False,
)


def init_db() -> None:
    with engine.begin() as conn:
        app_metadata.create_all(bind=conn)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
