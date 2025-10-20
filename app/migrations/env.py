from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

from app.config import get_settings
settings = get_settings()

# ---- Alembic config/logging ----
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# ---- Metadata for autogenerate ----
target_metadata = SQLModel.metadata

# ---- Build a SYNC URL for Alembic ----
def sync_url(url: str) -> str:
    # sqlite+aiosqlite:///./teski.db  -> sqlite:///./teski.db
    return url.replace("+aiosqlite", "")

from app.config import get_settings
SYNC_DB_URL = get_settings().DATABASE_URL.replace("+aiosqlite", "")

def run_migrations_offline() -> None:
    context.configure(
        url=SYNC_DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        render_as_batch=True,  # SQLite-friendly
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_engine(
        SYNC_DB_URL, poolclass=pool.NullPool, future=True
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()