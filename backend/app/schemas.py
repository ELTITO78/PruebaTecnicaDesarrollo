from pydantic import BaseModel, Field


class Pokemon(BaseModel):
    id: int
    name: str
    image: str | None
    types: list[str]


class PokemonPage(BaseModel):
    count: int
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    pages: int
    results: list[Pokemon]


class ErrorResponse(BaseModel):
    detail: str
