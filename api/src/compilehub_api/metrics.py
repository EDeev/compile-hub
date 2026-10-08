"""Метрики Prometheus: /metrics на порту API, наружу не проксируется (nginx отдаёт только /api)."""

import asyncio
import logging
import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from redis.asyncio import Redis

from .services import workers as workers_service
from .services.runs import queue_length

log = logging.getLogger(__name__)

REQUESTS = Histogram(
    "compilehub_api_request_seconds",
    "Время ответа API",
    ["method", "route", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
ERRORS = Counter("compilehub_api_errors_total", "Ответы с ошибкой по коду", ["code"])
RUNS_CREATED = Counter("compilehub_api_runs_created_total", "Поставленные запуски", ["language", "who", "interactive"])
RUN_RESULTS = Counter("compilehub_api_run_results_total", "Итоги запусков, записанные в БД", ["verdict"])
QUEUE = Gauge("compilehub_api_queue_length", "Задачи в очереди, включая выполняемые")
WORKERS = Gauge("compilehub_api_workers", "Живые воркеры")
WORKERS_PAUSED = Gauge("compilehub_api_workers_paused", "Воркеры на паузе по температуре")


def install(app: FastAPI) -> None:
    @app.middleware("http")
    async def _timing(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        if path != "/metrics":
            REQUESTS.labels(request.method, path, response.status_code).observe(time.perf_counter() - started)
        return response

    @app.get("/metrics", include_in_schema=False)
    async def _metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def refresh_gauges(redis: Redis) -> None:
    """Очередь и воркеры — раз в 10 с (сбор метрик синхронный, Redis из него не опросить)."""
    while True:
        try:
            QUEUE.set(await queue_length(redis))
            live = await workers_service.live(redis)
            WORKERS.set(len(live))
            WORKERS_PAUSED.set(sum(w.paused for w in live))
        except Exception:  # noqa: BLE001
            log.warning("метрики очереди не обновлены", exc_info=True)
        await asyncio.sleep(10)
