import httpx
import pytest

from app.cache import TTLCache
from app.client import PokeApiClient
from app.service import PokemonService

NAMES = ["bulbasaur", "ivysaur", "charmander", "squirtle", "pikachu"]
TYPES = {"bulbasaur": ["grass", "poison"], "ivysaur": ["grass", "poison"], "charmander": ["fire"], "squirtle": ["water"], "pikachu": ["electric"]}


def pokemon_payload(name: str) -> dict:
    return {
        "id": NAMES.index(name) + 1,
        "name": name,
        "sprites": {"front_default": f"{name}.png", "other": {"official-artwork": {"front_default": f"{name}-art.png"}}},
        "types": [{"slot": i + 1, "type": {"name": t}} for i, t in enumerate(TYPES[name])],
        "moves": [{"move": {"name": "tackle"}}],
    }


def pokeapi_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path.removeprefix("/api/v2")
    if path == "/pokemon":
        return httpx.Response(200, json={"results": [{"name": n} for n in NAMES]})
    if path == "/type":
        return httpx.Response(200, json={"results": [{"name": t} for t in ("grass", "fire", "unknown")]})
    if path.startswith("/type/"):
        type_name = path.split("/")[-1]
        if type_name not in {t for ts in TYPES.values() for t in ts}:
            return httpx.Response(404)
        return httpx.Response(200, json={"pokemon": [{"pokemon": {"name": n}} for n, ts in TYPES.items() if type_name in ts]})
    name = path.split("/")[-1]
    return httpx.Response(200, json=pokemon_payload(name)) if name in NAMES else httpx.Response(404)


class Recorder:
    def __init__(self, handler) -> None:
        self.handler = handler
        self.calls: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request.url.path)
        return self.handler(request)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def recorder() -> Recorder:
    return Recorder(pokeapi_handler)


@pytest.fixture
async def http(recorder):
    async with httpx.AsyncClient(base_url="https://pokeapi.test/api/v2", transport=httpx.MockTransport(recorder)) as client:
        yield client


@pytest.fixture
def client(http) -> PokeApiClient:
    return PokeApiClient(http, TTLCache(ttl=60, max_size=100), max_concurrency=2)


@pytest.fixture
def service(client) -> PokemonService:
    return PokemonService(client)
