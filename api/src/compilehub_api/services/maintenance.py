"""Чистка раз в 6 часов: история запусков, просроченные токены, неподтверждённые аккаунты.
Из нескольких реплик API работает одна — та, что взяла блокировку в Redis."""

import asyncio
import logging

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

log = logging.getLogger(__name__)

INTERVAL = 6 * 3600
LOCK = "maintenance:lock"

STATEMENTS = {
    "runs_old": "DELETE FROM runs WHERE created_at < now() - interval '90 days'"
    " OR (user_id IS NULL AND created_at < now() - interval '7 days')",
    "runs_over_200": """
        DELETE FROM runs WHERE id IN (
            SELECT id FROM (
                SELECT id, row_number() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS n
                FROM runs WHERE user_id IS NOT NULL
            ) ranked WHERE n > 200
        )""",
    "email_tokens": "DELETE FROM email_tokens WHERE expires_at < now() - interval '1 day'",
    "refresh_tokens": "DELETE FROM refresh_tokens WHERE expires_at < now() OR revoked_at < now() - interval '1 day'",
    "unverified_users": "DELETE FROM users WHERE email_verified_at IS NULL AND created_at < now() - interval '7 days'",
}


async def cleanup(session: AsyncSession) -> dict[str, int]:
    counts = {}
    for name, sql in STATEMENTS.items():
        counts[name] = (await session.execute(text(sql))).rowcount
    await session.commit()
    return counts


async def loop(sessionmaker: async_sessionmaker[AsyncSession], redis: Redis) -> None:
    while True:
        try:
            if await redis.set(LOCK, "1", nx=True, ex=INTERVAL - 60):
                async with sessionmaker() as session:
                    log.info("чистка: %s", await cleanup(session))
        except Exception:  # noqa: BLE001
            log.exception("чистка не удалась")
        await asyncio.sleep(INTERVAL)
