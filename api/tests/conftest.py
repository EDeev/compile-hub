"""Тесты API работают с настоящими Postgres и Redis: TEST_DATABASE_URL и TEST_REDIS_URL.
Без них тесты, которым нужна БД, пропускаются."""

import os
from collections.abc import AsyncIterator

import httpx2 as httpx
import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from compilehub_api.config import Settings
from compilehub_api.main import create_app
from compilehub_api.migrations import config as alembic_config

DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")
REDIS_URL = os.environ.get("TEST_REDIS_URL", "")
needs_services = pytest.mark.skipif(not (DATABASE_URL and REDIS_URL), reason="нужны TEST_DATABASE_URL и TEST_REDIS_URL")

TABLES = "runs, files, folders, user_settings, user_limits, email_tokens, refresh_tokens, users"


def settings(**overrides) -> Settings:
    base = {
        "database_url": DATABASE_URL,
        "redis_url": REDIS_URL,
        "jwt_secret": "test-secret-test-secret-test-secret",
        "public_url": "https://compilehub.test",
        "cookie_secure": False,
        "maintenance": False,
        "yandex_client_id": "ya-id",
        "yandex_client_secret": "ya-secret",
    }
    return Settings(**(base | overrides))


async def reset_schema() -> None:
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


@pytest.fixture(scope="session")
async def migrated() -> None:
    if not DATABASE_URL:
        pytest.skip("нужен TEST_DATABASE_URL")
    await reset_schema()
    await _upgrade("head")


async def _upgrade(rev: str) -> None:
    import asyncio

    await asyncio.to_thread(command.upgrade, alembic_config(DATABASE_URL), rev)


@pytest.fixture
async def app(migrated):
    application = create_app(settings())
    async with application.router.lifespan_context(application):
        async with application.state.sessionmaker() as session:
            await session.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
            await session.commit()
        await application.state.redis.flushdb()
        yield application


@pytest.fixture
async def client(app) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
