import pytest

pytestmark = pytest.mark.anyio


async def test_paginates_results(service):
    page = await service.search(page=2, size=2)
    assert [p.name for p in page.results] == ["charmander", "squirtle"]
    assert (page.count, page.pages) == (5, 3)


async def test_searches_by_partial_name(service):
    page = await service.search(page=1, size=20, name=" SAUR ")
    assert [p.name for p in page.results] == ["bulbasaur", "ivysaur"]


async def test_filters_by_type(service):
    page = await service.search(page=1, size=20, type_name="fire")
    assert [p.name for p in page.results] == ["charmander"]


async def test_combines_name_and_type(service):
    page = await service.search(page=1, size=20, name="ivy", type_name="grass")
    assert [p.id for p in page.results] == [2]


async def test_unknown_type_returns_empty_page(service):
    page = await service.search(page=1, size=20, type_name="dragon")
    assert page.count == 0 and page.results == []


async def test_page_out_of_range_is_empty(service):
    page = await service.search(page=10, size=20)
    assert page.results == []


async def test_excludes_non_playable_types(service):
    assert await service.types() == ["grass", "fire"]
