import asyncio

import httpx2 as httpx
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy.ext.asyncio import create_async_engine

from compilehub_api.main import create_app
from compilehub_api.migrations import config as alembic_config
from compilehub_api.models import Base
from compilehub_protocol import WorkerInfo

from .conftest import DATABASE_URL, needs_services, reset_schema, settings

pytestmark = needs_services


async def _diff() -> list:
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        diff = await conn.run_sync(lambda c: compare_metadata(MigrationContext.configure(c), Base.metadata))
    await engine.dispose()
    return diff


async def test_migrations_roundtrip_and_match_models():
    await reset_schema()
    cfg = alembic_config(DATABASE_URL)
    await asyncio.to_thread(command.upgrade, cfg, "head")
    await asyncio.to_thread(command.downgrade, cfg, "base")
    await asyncio.to_thread(command.upgrade, cfg, "head")
    # индекс по выражению alembic не сравнивает — остальное должно совпасть полностью
    assert await _diff() == []


async def test_health_ok(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": True, "redis": True, "workers": 0, "paused": False}


async def test_health_counts_workers_and_pause(app, client):
    info = WorkerInfo(name="w1", slots=1, busy=0, languages={"python": "3.12"}, paused=True)
    await app.state.redis.set("workers:w1", info.dump(), ex=15)
    assert (await client.get("/api/health")).json() | {} == {
        "status": "ok",
        "db": True,
        "redis": True,
        "workers": 1,
        "paused": True,
    }


async def test_health_fails_without_redis(migrated):
    app = create_app(settings(redis_url="redis://127.0.0.1:1/0"))
    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/api/health")
    assert r.status_code == 503
    assert r.json()["redis"] is False and r.json()["db"] is True


async def test_unknown_route_uses_error_format(client):
    r = await client.get("/api/nope")
    assert r.status_code == 404
    assert r.json() == {"error": {"code": "not_found", "message": "Not Found"}}


async def test_metrics(client):
    await client.get("/api/nope")
    await client.post("/api/runs", json={"language": "python", "code": ""})  # нет воркеров — 503 no_workers
    text = (await client.get("/metrics")).text
    assert 'compilehub_api_errors_total{code="no_workers"}' in text
    assert 'compilehub_api_request_seconds_count{method="POST",route="/api/runs",status="503"}' in text
    assert "compilehub_api_queue_length" in text
