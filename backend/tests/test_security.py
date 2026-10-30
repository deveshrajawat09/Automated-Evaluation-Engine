import pytest

from app.core.config import Settings
from app.core.rate_limit import FixedWindowLimiter


def test_auth_limiter_rejects_after_limit():
    limiter = FixedWindowLimiter(limit=2, window_seconds=60)

    assert limiter.allow("client")
    assert limiter.allow("client")
    assert not limiter.allow("client")
    assert limiter.allow("other-client")


def test_production_requires_non_default_jwt_secret():
    settings = Settings(environment="production", jwt_secret="change-me-in-production")

    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        settings.validate()


def test_development_allows_default_jwt_secret():
    Settings(environment="development", jwt_secret="change-me-in-production").validate()


def test_redis_limiter_uses_atomic_counter(monkeypatch):
    from app.core import rate_limit

    class FakePipeline:
        def __init__(self):
            self.commands = []

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def incr(self, key):
            self.commands.append(("incr", key))

        def expire(self, key, seconds):
            self.commands.append(("expire", key, seconds))

        def execute(self):
            return [1, True]

    class FakeRedis:
        def pipeline(self):
            return FakePipeline()

    limiter = object.__new__(rate_limit.RedisLimiter)
    limiter.client = FakeRedis()
    limiter.limit = 1
    limiter.window_seconds = 60
    assert limiter.allow("client")
