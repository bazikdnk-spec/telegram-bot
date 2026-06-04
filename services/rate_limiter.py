"""Task 3: Multi-level Token Bucket rate limiter with Redis / in-memory fallback."""
import time
import asyncio
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False


@dataclass
class TokenBucket:
    capacity: float
    refill_rate: float  # tokens per second
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)

    def __post_init__(self):
        self._tokens = self.capacity
        self._last_refill = time.monotonic()

    def consume(self, tokens: float = 1.0) -> bool:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False


class InMemoryRateLimiter:
    """In-memory fallback when Redis is unavailable."""

    def __init__(self, user_rpm: int, chat_rpm: int, global_rpm: int):
        self._user_buckets: dict[int, TokenBucket] = {}
        self._chat_buckets: dict[int, TokenBucket] = {}
        self._global_bucket = TokenBucket(
            capacity=global_rpm,
            refill_rate=global_rpm / 60.0,
        )
        self._user_rpm = user_rpm
        self._chat_rpm = chat_rpm
        self._global_rpm = global_rpm
        self._lock = asyncio.Lock()

    async def check(self, user_id: int, chat_id: int) -> tuple[bool, str]:
        async with self._lock:
            if user_id not in self._user_buckets:
                self._user_buckets[user_id] = TokenBucket(
                    capacity=self._user_rpm,
                    refill_rate=self._user_rpm / 60.0,
                )
            if chat_id not in self._chat_buckets:
                self._chat_buckets[chat_id] = TokenBucket(
                    capacity=self._chat_rpm,
                    refill_rate=self._chat_rpm / 60.0,
                )

            if not self._user_buckets[user_id].consume():
                return False, f"Превышен лимит: {self._user_rpm} запросов/минуту на пользователя."
            if not self._chat_buckets[chat_id].consume():
                return False, f"Превышен лимит чата: {self._chat_rpm} запросов/минуту."
            if not self._global_bucket.consume():
                return False, "Глобальный лимит API исчерпан. Попробуйте через минуту."
            return True, ""


class RedisRateLimiter:
    """Redis-based Token Bucket via Lua script (atomic)."""

    LUA_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

local elapsed = now - last_refill
tokens = math.min(capacity, tokens + elapsed * refill_rate)

if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 120)
    return 1
else
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 120)
    return 0
end
"""

    def __init__(self, redis_client, user_rpm: int, chat_rpm: int, global_rpm: int):
        self._redis = redis_client
        self._user_rpm = user_rpm
        self._chat_rpm = chat_rpm
        self._global_rpm = global_rpm
        self._script = None

    async def _get_script(self):
        if self._script is None:
            self._script = self._redis.register_script(self.LUA_SCRIPT)
        return self._script

    async def _check_bucket(self, key: str, capacity: int, rpm: int) -> bool:
        script = await self._get_script()
        now = time.time()
        refill_rate = rpm / 60.0
        result = await script(keys=[key], args=[capacity, refill_rate, now])
        return bool(result)

    async def check(self, user_id: int, chat_id: int) -> tuple[bool, str]:
        if not await self._check_bucket(f"rl:user:{user_id}", self._user_rpm, self._user_rpm):
            return False, f"Превышен лимит: {self._user_rpm} запросов/минуту на пользователя."
        if not await self._check_bucket(f"rl:chat:{chat_id}", self._chat_rpm, self._chat_rpm):
            return False, f"Превышен лимит чата: {self._chat_rpm} запросов/минуту."
        if not await self._check_bucket("rl:global", self._global_rpm, self._global_rpm):
            return False, "Глобальный лимит API исчерпан. Попробуйте через минуту."
        return True, ""


async def create_rate_limiter(settings) -> InMemoryRateLimiter | RedisRateLimiter:
    if _REDIS_AVAILABLE:
        try:
            client = aioredis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True,
            )
            await client.ping()
            logger.info("Rate limiter: используется Redis")
            return RedisRateLimiter(
                client,
                settings.rate_limit_per_user,
                settings.rate_limit_per_chat,
                settings.rate_limit_global_rpm,
            )
        except Exception as e:
            logger.warning(f"Redis недоступен ({e}), используется in-memory rate limiter")

    return InMemoryRateLimiter(
        settings.rate_limit_per_user,
        settings.rate_limit_per_chat,
        settings.rate_limit_global_rpm,
    )
