from pydantic import ValidationError
from redis.asyncio import Redis

from compilehub_protocol import WorkerInfo, worker_key


async def live(redis: Redis) -> list[WorkerInfo]:
    """Живые воркеры — те, чьё сердцебиение `workers:{name}` ещё не истекло."""
    keys = [k async for k in redis.scan_iter(worker_key("*"), count=100)]
    if not keys:
        return []
    out = []
    for raw in await redis.mget(keys):
        if raw:
            try:
                out.append(WorkerInfo.model_validate_json(raw))
            except ValidationError:
                continue
    return out


def all_paused(workers: list[WorkerInfo]) -> bool:
    return bool(workers) and all(w.paused for w in workers)
