"""Лимиты по умолчанию (ARCHITECTURE.md, «Лимиты по умолчанию») и фактическое использование."""

from dataclasses import dataclass
from datetime import UTC, datetime

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import File, Folder, User
from ..schemas import LimitsOut, UsageOut

KB = 1024


@dataclass(frozen=True)
class Limits:
    max_files: int | None
    max_folders: int | None
    max_code_bytes: int
    runs_per_minute: int | None
    runs_per_day: int | None


GUEST = Limits(max_files=10, max_folders=3, max_code_bytes=64 * KB, runs_per_minute=6, runs_per_day=100)
UNVERIFIED = Limits(max_files=10, max_folders=3, max_code_bytes=64 * KB, runs_per_minute=10, runs_per_day=200)
USER = Limits(max_files=100, max_folders=20, max_code_bytes=64 * KB, runs_per_minute=30, runs_per_day=1000)
ADMIN = Limits(max_files=None, max_folders=None, max_code_bytes=256 * KB, runs_per_minute=None, runs_per_day=None)


def for_user(user: User) -> Limits:
    base = ADMIN if user.role == "admin" else USER if user.verified else UNVERIFIED
    own = user.limits
    if own is None:
        return base
    return Limits(
        max_files=own.max_files if own.max_files is not None else base.max_files,
        max_folders=own.max_folders if own.max_folders is not None else base.max_folders,
        max_code_bytes=own.max_code_bytes if own.max_code_bytes is not None else base.max_code_bytes,
        runs_per_minute=base.runs_per_minute,
        runs_per_day=own.runs_per_day if own.runs_per_day is not None else base.runs_per_day,
    )


def quota_key(scope: str) -> str:
    """Суточный счётчик запусков; scope — user:{id} или ip:{ip}; сутки по UTC."""
    return f"quota:runs:{scope}:{datetime.now(UTC):%Y-%m-%d}"


async def usage(session: AsyncSession, redis: Redis, user: User) -> UsageOut:
    files = await session.scalar(select(func.count()).select_from(File).where(File.user_id == user.id))
    folders = await session.scalar(select(func.count()).select_from(Folder).where(Folder.user_id == user.id))
    runs = await redis.get(quota_key(f"user:{user.id}"))
    return UsageOut(files=files or 0, folders=folders or 0, runs_today=int(runs or 0))


def limits_out(limits: Limits) -> LimitsOut:
    return LimitsOut(**limits.__dict__)
