from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis as _Redis


def make_redis(url: str) -> _Redis:
    # таймаут сокета больше любого XREAD/XREADGROUP BLOCK (до 15 с), иначе блокирующее чтение обрывается
    return _Redis.from_url(url, decode_responses=True, health_check_interval=30, socket_timeout=30)


def _redis(request: Request) -> _Redis:
    return request.app.state.redis


Redis = Annotated[_Redis, Depends(_redis)]
