import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, async_engine_from_config

from app.config.settings import get_settings
from app.core.db.base import Base
from app.domain.contact import models as contact_models  # noqa: F401
from app.domain.link import models as link_models  # noqa: F401
from app.domain.media import models as media_models  # noqa: F401
from app.domain.profile import models as profile_models  # noqa: F401
from app.domain.subscription import models as subscription_models  # noqa: F401
from app.domain.theme import models as theme_models  # noqa: F401
from app.domain.user import models as user_models  # noqa: F401

config = context.config
settings = get_settings()
target_metadata = Base.metadata

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    url = settings.DATABASE_URL.get_secret_value().replace(
        "postgresql+asyncpg", "postgresql+psycopg2"
    )
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: AsyncConnection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in online mode using an async engine."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL.get_secret_value()

    connectable: AsyncEngine = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
