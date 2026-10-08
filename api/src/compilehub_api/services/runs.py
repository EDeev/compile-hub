"""Очередь запусков: постановка задачи, позиция, приём итогов от воркеров в БД."""

import asyncio
import contextlib
import logging
import os
import socket
from datetime import UTC, datetime
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import ResponseError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from compilehub_protocol import FIELD, QUEUE, RESULTS, RESULTS_GROUP, Result

from ..models import Run

log = logging.getLogger(__name__)

CONSUMER = f"{socket.gethostname()}-{os.getpid()}"
RECLAIM_IDLE_MS = 60_000


async def queue_length(redis: Redis) -> int:
    """Задачи в очереди, включая выполняемые: воркер удаляет запись только после завершения."""
    return await redis.xlen(QUEUE)


async def save_result(session: AsyncSession, result: Result) -> None:
    await session.execute(
        update(Run)
        .where(Run.id == result.run_id)
        .values(
            verdict=result.verdict.value,
            exit_code=result.exit_code,
            signal=result.signal,
            time_ms=result.time_ms,
            memory_kb=result.memory_kb,
            output=result.output,
            finished_at=datetime.now(UTC),
        )
    )


async def ensure_group(redis: Redis) -> None:
    with contextlib.suppress(ResponseError):  # BUSYGROUP — уже есть
        await redis.xgroup_create(RESULTS, RESULTS_GROUP, id="0", mkstream=True)


async def collect_results(sessionmaker: async_sessionmaker[AsyncSession], redis: Redis, on_result=None) -> None:
    """Фоновая задача API: итоги из runs:results → таблица runs. Группа общая для всех реплик API."""
    claimed_at = 0.0
    group_ready = False
    loop = asyncio.get_running_loop()
    while True:
        try:
            if not group_ready:  # Redis может быть ещё недоступен при старте — пробуем в цикле
                await ensure_group(redis)
                group_ready = True
            batch = []
            if loop.time() - claimed_at > 30:  # итоги, которые взяла и не дописала упавшая реплика
                _, batch, _ = await redis.xautoclaim(
                    RESULTS, RESULTS_GROUP, CONSUMER, RECLAIM_IDLE_MS, "0-0", count=100
                )
                claimed_at = loop.time()
            if not batch:
                response = await redis.xreadgroup(RESULTS_GROUP, CONSUMER, {RESULTS: ">"}, count=100, block=5000)
                batch = response[0][1] if response else []
            if not batch:
                continue
            results = [(msg_id, Result.model_validate_json(fields[FIELD])) for msg_id, fields in batch]
            async with sessionmaker() as session:
                for _, result in results:
                    await save_result(session, result)
                await session.commit()
            ids = [msg_id for msg_id, _ in results]
            await redis.xack(RESULTS, RESULTS_GROUP, *ids)
            await redis.xdel(RESULTS, *ids)
            if on_result:
                for _, result in results:
                    on_result(result)
        except asyncio.CancelledError:
            raise
        except ResponseError as e:
            if "NOGROUP" not in str(e):
                raise
            await ensure_group(redis)  # Redis перезапустился без данных — группу заводим заново
        except Exception:  # noqa: BLE001
            log.exception("приём итогов не удался")
            await asyncio.sleep(2)


def parse_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None
