import asyncio
from typing import Any

import httpx

from app.cache import TTLCache


class PokeApiError(Exception):
    pass


class PokemonNotFound(Exception):
    pass


class PokeApiClient:
    def __init__(self, http: httpx.AsyncClient, cache: TTLCache, max_concurrency: int) -> None:
        self._http = http
        self._cache = cache
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def _get(self, path: str) -> dict[str, Any]:
        return await self._cache.get_or_load(path, lambda: self._fetch(path))

    async def _fetch(self, path: str) -> dict[str, Any]:
        async with self._semaphore:
            try:
                response = await self._http.get(path)
            except httpx.HTTPError as exc:
                raise PokeApiError("PokéAPI no está disponible") from exc
        if response.status_code == httpx.codes.NOT_FOUND:
            raise PokemonNotFound(path)
        if response.is_error:
            raise PokeApiError(f"PokéAPI respondió con estado {response.status_code}")
        return response.json()

    async def list_names(self) -> list[str]:
        data = await self._get("/pokemon?limit=100000&offset=0")
        return [item["name"] for item in data["results"]]

    async def list_types(self) -> list[str]:
        data = await self._get("/type?limit=100")
        return [item["name"] for item in data["results"]]

    async def names_by_type(self, type_name: str) -> set[str]:
        data = await self._get(f"/type/{type_name}")
        return {entry["pokemon"]["name"] for entry in data["pokemon"]}

    async def pokemon(self, name: str) -> dict[str, Any]:
        return await self._get(f"/pokemon/{name}")
