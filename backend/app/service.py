import asyncio
import math
from typing import Any

from app.client import PokeApiClient, PokemonNotFound
from app.schemas import Pokemon, PokemonPage


def to_pokemon(raw: dict[str, Any]) -> Pokemon:
    sprites = raw.get("sprites") or {}
    artwork = sprites.get("other", {}).get("official-artwork", {}).get("front_default")
    return Pokemon(
        id=raw["id"],
        name=raw["name"],
        image=artwork or sprites.get("front_default"),
        types=[slot["type"]["name"] for slot in sorted(raw["types"], key=lambda slot: slot["slot"])],
    )


class PokemonService:
    def __init__(self, client: PokeApiClient) -> None:
        self._client = client

    async def search(self, page: int, size: int, name: str | None = None, type_name: str | None = None) -> PokemonPage:
        names = await self._client.list_names()
        if name:
            term = name.strip().lower()
            names = [candidate for candidate in names if term in candidate]
        if type_name:
            try:
                allowed = await self._client.names_by_type(type_name.lower())
            except PokemonNotFound:
                allowed = set()
            names = [candidate for candidate in names if candidate in allowed]

        start = (page - 1) * size
        selected = names[start:start + size]
        details = await asyncio.gather(*(self._client.pokemon(candidate) for candidate in selected))
        return PokemonPage(
            count=len(names),
            page=page,
            size=size,
            pages=math.ceil(len(names) / size),
            results=[to_pokemon(raw) for raw in details],
        )

    async def get(self, identifier: str) -> Pokemon:
        return to_pokemon(await self._client.pokemon(identifier.strip().lower()))

    async def types(self) -> list[str]:
        excluded = {"unknown", "shadow", "stellar"}
        return [name for name in await self._client.list_types() if name not in excluded]
