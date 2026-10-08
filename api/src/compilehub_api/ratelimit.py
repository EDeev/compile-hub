"""Token bucket в Redis одним Lua-скриптом: атомарно и общий для всех реплик API."""

from redis.asyncio import Redis

from .errors import ApiError

# KEYS[1] — ведро; ARGV: ёмкость, токенов в секунду, стоимость. Время — часы Redis.
_LUA = """
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])
local t = redis.call('TIME')
local now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)
local b = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local tokens = tonumber(b[1]) or capacity
local ts = tonumber(b[2]) or now
tokens = math.min(capacity, tokens + (now - ts) / 1000 * rate)
local allowed = 0
local wait = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
else
  wait = math.ceil((cost - tokens) / rate * 1000)
end
redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', now)
redis.call('PEXPIRE', KEYS[1], math.ceil(capacity / rate * 1000) + 1000)
return {allowed, wait}
"""


async def hit(redis: Redis, key: str, capacity: int, per_seconds: float, cost: int = 1) -> None:
    """Списать cost из ведра «capacity за per_seconds»; не хватает — 429 rate_limited с Retry-After."""
    allowed, wait_ms = await redis.eval(_LUA, 1, f"rl:{key}", capacity, capacity / per_seconds, cost)
    if not allowed:
        retry = max(1, -(-int(wait_ms) // 1000))
        raise ApiError(
            429, "rate_limited", "Too many requests", {"retryAfter": retry}, headers={"Retry-After": str(retry)}
        )
