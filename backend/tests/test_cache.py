import asyncio

import pytest

from app.cache import TTLCache


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_returns_value_before_expiration():
    clock = FakeClock()
    cache = TTLCache(ttl=10, max_size=10, clock=clock)
    cache.set("a", 1)
    clock.now = 9
    assert cache.get("a") == 1


def test_expires_after_ttl():
    clock = FakeClock()
    cache = TTLCache(ttl=10, max_size=10, clock=clock)
    cache.set("a", 1)
    clock.now = 11
    assert cache.get("a") is None
    assert len(cache) == 0


def test_evicts_least_recently_used():
    cache = TTLCache(ttl=10, max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")
    cache.set("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1


@pytest.mark.anyio
async def test_concurrent_loads_share_single_call():
    cache = TTLCache(ttl=10, max_size=10)
    calls = 0

    async def loader():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return "value"

    results = await asyncio.gather(*(cache.get_or_load("k", loader) for _ in range(5)))
    assert results == ["value"] * 5
    assert calls == 1


@pytest.mark.anyio
async def test_failed_load_is_not_cached():
    cache = TTLCache(ttl=10, max_size=10)

    async def failing():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await cache.get_or_load("k", failing)
    assert cache.get("k") is None
