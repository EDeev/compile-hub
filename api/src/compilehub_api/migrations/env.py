import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from compilehub_api.config import get_settings
from compilehub_api.models import Base

config = context.config


def _run(connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def _main() -> None:
    url = config.attributes.get("database_url") or get_settings().database_url
    engine = create_async_engine(url)
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


asyncio.run(_main())
