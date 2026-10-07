from fastapi import APIRouter, Response
from sqlalchemy import text

from compilehub_protocol import PAUSED_KEY

from ..db import Session
from ..redis import Redis

router = APIRouter()


@router.get("/api/health")
async def health(session: Session, redis: Redis, response: Response) -> dict:
    """Живость: 200, если доступны Postgres и Redis; число живых воркеров и пауза — для информации."""
    db_ok = redis_ok = False
    workers, paused = 0, False
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        pass
    try:
        workers = len([k async for k in redis.scan_iter("workers:*") if k != PAUSED_KEY])
        paused = bool(await redis.exists(PAUSED_KEY))
        redis_ok = True
    except Exception:  # noqa: BLE001
        pass
    ok = db_ok and redis_ok
    if not ok:
        response.status_code = 503
    return {"status": "ok" if ok else "fail", "db": db_ok, "redis": redis_ok, "workers": workers, "paused": paused}
