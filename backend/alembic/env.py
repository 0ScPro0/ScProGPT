import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent  # backend/
sys.path.insert(0, str(backend_dir / "src"))  # <- Нужно получить backend/src

from src.database import Base

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
from src.core.config import settings
import os

# Ensure the database directory exists
db_url = settings.database.url
if db_url.startswith("sqlite"):
    # Extract the path from the SQLite URL
    if "///" in db_url:
        db_path = db_url.split("///")[-1]
        if db_path.startswith("./"):
            db_path = db_path[2:]  # Remove the ./ prefix
        # Create the full path relative to the backend directory
        full_db_path = os.path.join(os.path.dirname(__file__), "..", db_path)
        # Ensure the directory exists
        db_dir = os.path.dirname(full_db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        # Update the URL with the absolute path
        db_url = f"sqlite+aiosqlite:///{os.path.abspath(full_db_path)}"

config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
