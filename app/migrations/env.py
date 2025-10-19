from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path
from typing import Optional

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.db import db_url
from app.models import app_metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None and Path(config.config_file_name).exists():
    fileConfig(config.config_file_name)

target_metadata = app_metadata


def _run_migrations_offline() -> None:
    url = db_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def _run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = db_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    _run_migrations_offline()
else:
    _run_migrations_online()
