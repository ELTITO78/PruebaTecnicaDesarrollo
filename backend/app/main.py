from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.cache import TTLCache
from app.client import PokeApiClient, PokeApiError, PokemonNotFound
from app.config import get_settings
from app.schemas import ErrorResponse, Pokemon, PokemonPage
from app.service import PokemonService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    async with httpx.AsyncClient(base_url=settings.pokeapi_url, timeout=settings.request_timeout) as http:
        cache = TTLCache(settings.cache_ttl, settings.cache_max_size)
        app.state.service = PokemonService(PokeApiClient(http, cache, settings.max_concurrency))
        yield


app = FastAPI(title="Pokédex API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins, allow_methods=["GET"])


@app.exception_handler(PokeApiError)
async def pokeapi_error_handler(_: Request, exc: PokeApiError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(PokemonNotFound)
async def not_found_handler(_: Request, __: PokemonNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Pokémon no encontrado"})


def get_service(request: Request) -> PokemonService:
    return request.app.state.service


Service = Annotated[PokemonService, Depends(get_service)]
errors = {404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}}


@app.get("/api/pokemon", response_model=PokemonPage, responses=errors)
async def list_pokemon(
    service: Service,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    name: Annotated[str | None, Query(max_length=50)] = None,
    type: Annotated[str | None, Query(max_length=20)] = None,
) -> PokemonPage:
    return await service.search(page, size, name, type)


@app.get("/api/pokemon/{identifier}", response_model=Pokemon, responses=errors)
async def get_pokemon(service: Service, identifier: str) -> Pokemon:
    return await service.get(identifier)


@app.get("/api/types", response_model=list[str], responses=errors)
async def list_types(service: Service) -> list[str]:
    return await service.types()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if get_settings().frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=get_settings().frontend_dir, html=True), name="frontend")
