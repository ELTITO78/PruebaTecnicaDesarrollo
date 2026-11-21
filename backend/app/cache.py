import asyncio
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from typing import Any


class TTLCache:
    def __init__(self, ttl: float, max_size: int, clock: Callable[[], float] = time.monotonic) -> None:
        self._ttl = ttl
        self._max_size = max_size
        self._clock = clock
        self._data: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._inflight: dict[str, asyncio.Future[Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at < self._clock():
            del self._data[key]
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        self._data[key] = (self._clock() + self._ttl, value)
        self._data.move_to_end(key)
        while len(self._data) > self._max_size:
            self._data.popitem(last=False)

    async def get_or_load(self, key: str, loader: Callable[[], Awaitable[Any]]) -> Any:
        if (cached := self.get(key)) is not None:
            return cached
        if key in self._inflight:
            return await self._inflight[key]
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._inflight[key] = future
        try:
            value = await loader()
            self.set(key, value)
            future.set_result(value)
            return value
        except Exception as exc:
            future.set_exception(exc)
            future.exception()
            raise
        finally:
            del self._inflight[key]

    def __len__(self) -> int:
        return len(self._data)
