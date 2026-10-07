from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis as _Redis


def make_redis(url: str) -> _Redis:
    return _Redis.from_url(url, decode_responses=True, health_check_interval=30)


def _redis(request: Request) -> _Redis:
    return request.app.state.redis


Redis = Annotated[_Redis, Depends(_redis)]
