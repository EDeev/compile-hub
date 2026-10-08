import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import errors, metrics
from .config import Settings, get_settings
from .db import make_engine, make_sessionmaker
from .mail import Mailer
from .redis import make_redis
from .routers import auth, files, health, me, oauth, runs
from .services import maintenance
from .services.runs import collect_results


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(settings.database_url)
        app.state.sessionmaker = make_sessionmaker(engine)
        app.state.redis = make_redis(settings.redis_url)
        on_result = lambda result: metrics.RUN_RESULTS.labels(result.verdict.value).inc()  # noqa: E731
        tasks = [
            asyncio.create_task(collect_results(app.state.sessionmaker, app.state.redis, on_result)),
            asyncio.create_task(metrics.refresh_gauges(app.state.redis)),
        ]
        if settings.maintenance:
            tasks.append(asyncio.create_task(maintenance.loop(app.state.sessionmaker, app.state.redis)))
        yield
        for task in tasks:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await app.state.redis.aclose()
        await engine.dispose()

    app = FastAPI(
        title="CompileHub API",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.mailer = Mailer(settings)
    errors.install(app)
    metrics.install(app)
    for module in (health, auth, oauth, me, files, runs):
        app.include_router(module.router)
    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
