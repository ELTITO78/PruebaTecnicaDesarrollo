import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app, get_service
from app.cache import TTLCache
from app.client import PokeApiClient
from app.service import PokemonService
from tests.conftest import pokeapi_handler


def build_client(handler) -> TestClient:
    http = httpx.AsyncClient(base_url="https://pokeapi.test/api/v2", transport=httpx.MockTransport(handler))
    service = PokemonService(PokeApiClient(http, TTLCache(60, 100), 5))
    app.dependency_overrides[get_service] = lambda: service
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_overrides():
    yield
    app.dependency_overrides.clear()


def test_lists_pokemon():
    response = build_client(pokeapi_handler).get("/api/pokemon", params={"size": 2})
    assert response.status_code == 200
    assert response.json()["results"][0] == {"id": 1, "name": "bulbasaur", "image": "bulbasaur-art.png", "types": ["grass", "poison"]}


def test_returns_404_for_unknown_pokemon():
    response = build_client(pokeapi_handler).get("/api/pokemon/missingno")
    assert response.status_code == 404
    assert response.json() == {"detail": "Pokémon no encontrado"}


def test_returns_503_when_pokeapi_is_down():
    response = build_client(lambda _: httpx.Response(502)).get("/api/pokemon")
    assert response.status_code == 503


def test_validates_query_parameters():
    assert build_client(pokeapi_handler).get("/api/pokemon", params={"size": 500}).status_code == 422
