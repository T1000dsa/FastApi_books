from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from src.database_data.settings import get_db_url_sync, get_db_url_async
from src.database_data.models import *#BookModelOrm, TagsModelOrm, TagsOnBookOrm
from src.database_data.models import Base
from src.database_data.database import sync_engine, async_engine
# alembic revision --autogenerate
# alembic upgrade head


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

url = get_db_url_async()
config.set_main_option('sqlalchemy.url', url + '?async_fallback=True') # + '?async_fallback=True'

target_metadata = Base.metadata
print(config.get_main_option('sqlalchemy.url'))

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
