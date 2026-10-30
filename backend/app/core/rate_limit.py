from __future__ import annotations

from collections import deque
from threading import Lock
from time import monotonic
from os import getenv


class FixedWindowLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._attempts: dict[str, deque[float]] = {}
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            attempts = self._attempts.setdefault(key, deque())
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if len(attempts) >= self.limit:
                return False
            attempts.append(now)
            return True


class RedisLimiter:
    def __init__(self, url: str, limit: int, window_seconds: int) -> None:
        from redis import Redis
        from redis.exceptions import RedisError

        self.client = Redis.from_url(url, decode_responses=True)
        self.redis_error = RedisError
        self.limit = limit
        self.window_seconds = window_seconds

    def allow(self, key: str) -> bool:
        redis_key = f"hackeval:rate-limit:{key}"
        try:
            with self.client.pipeline() as pipeline:
                pipeline.incr(redis_key)
                pipeline.expire(redis_key, self.window_seconds)
                count, _ = pipeline.execute()
        except self.redis_error as error:
            raise RuntimeError("Redis rate limiter is unavailable") from error
        return int(count) <= self.limit


def create_auth_limiter() -> RedisLimiter | FixedWindowLimiter:
    redis_url = getenv("REDIS_URL", "")
    if redis_url:
        return RedisLimiter(redis_url, limit=10, window_seconds=60)
    return FixedWindowLimiter(limit=10, window_seconds=60)


auth_limiter = create_auth_limiter()
