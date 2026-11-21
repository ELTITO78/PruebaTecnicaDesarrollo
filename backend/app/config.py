from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POKEDEX_", env_file=".env", extra="ignore")

    pokeapi_url: str = "https://pokeapi.co/api/v2"
    request_timeout: float = 10.0
    max_concurrency: int = 10
    cache_ttl: int = 3600
    cache_max_size: int = 2048
    cors_origins: list[str] = ["*"]
    frontend_dir: Path = Path(__file__).resolve().parents[2] / "frontend"


@lru_cache
def get_settings() -> Settings:
    return Settings()
