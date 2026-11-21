import asyncio

import httpx
import pytest

from app.cache import TTLCache
from app.client import PokeApiClient, PokeApiError, PokemonNotFound
from app.service import to_pokemon
from tests.conftest import pokemon_payload

pytestmark = pytest.mark.anyio


def test_maps_external_payload_to_dto():
    pokemon = to_pokemon(pokemon_payload("bulbasaur"))
    assert pokemon.model_dump() == {"id": 1, "name": "bulbasaur", "image": "bulbasaur-art.png", "types": ["grass", "poison"]}


def test_falls_back_to_default_sprite():
    payload = pokemon_payload("pikachu") | {"sprites": {"front_default": "pikachu.png", "other": {}}}
    assert to_pokemon(payload).image == "pikachu.png"


async def test_caches_repeated_requests(client, recorder):
    await client.pokemon("pikachu")
    await client.pokemon("pikachu")
    assert recorder.calls.count("/api/v2/pokemon/pikachu") == 1


async def test_raises_not_found(client):
    with pytest.raises(PokemonNotFound):
        await client.pokemon("missingno")


async def test_translates_server_errors():
    transport = httpx.MockTransport(lambda _: httpx.Response(500))
    async with httpx.AsyncClient(base_url="https://pokeapi.test", transport=transport) as http:
        with pytest.raises(PokeApiError):
            await PokeApiClient(http, TTLCache(60, 10), 2).pokemon("pikachu")


async def test_translates_network_errors():
    def handler(request):
        raise httpx.ConnectTimeout("timeout", request=request)

    async with httpx.AsyncClient(base_url="https://pokeapi.test", transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(PokeApiError):
            await PokeApiClient(http, TTLCache(60, 10), 2).pokemon("pikachu")


async def test_limits_parallel_requests():
    active = peak = 0

    async def handler(request):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(base_url="https://pokeapi.test", transport=httpx.MockTransport(handler)) as http:
        client = PokeApiClient(http, TTLCache(60, 100), max_concurrency=3)
        await asyncio.gather(*(client.pokemon(str(i)) for i in range(10)))
    assert peak == 3
