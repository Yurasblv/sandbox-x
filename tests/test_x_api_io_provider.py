from typing import Any

from collector.core.config import XSettings
from collector.providers.x_api_io import XAPIIOProvider
from collector.providers.x_api_io_utils import map_account


def test_map_account_accepts_common_username_aliases() -> None:
    account = map_account({"id": "1", "screen_name": "openai", "name": "OpenAI"})

    assert account.username == "openai"


async def test_search_accounts_skips_invalid_user_items() -> None:
    provider = object.__new__(XAPIIOProvider)
    provider.settings = XSettings(api_key="test-api-key")

    async def collect_pages(
        path: str,
        *,
        params: dict[str, Any],
        item_key: str,
        limit: int,
    ) -> dict[str, Any]:
        assert path == "/twitter/user/search"
        assert params == {"query": "ai"}
        assert item_key == "users"
        assert limit == 3
        return {
            "items": [
                {"id": "1", "userName": "openai", "name": "OpenAI"},
                {"id": "2", "name": "Missing username"},
                {"id": "3", "screen_name": "legacy", "name": "Legacy"},
            ],
            "pages": [],
            "next_cursor": None,
            "has_next_page": False,
        }

    provider._collect_pages = collect_pages

    result = await provider.search_accounts("ai", limit=3)

    assert [account.username for account in result.accounts] == ["openai", "legacy"]
    assert len(result.errors) == 1
    assert result.errors[0].source == "2"


async def test_collect_pages_stops_after_empty_page() -> None:
    provider = object.__new__(XAPIIOProvider)
    provider.settings = XSettings(api_key="test-api-key")
    calls: list[dict[str, Any]] = []

    async def get(path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        calls.append(params)
        return {
            "tweets": [],
            "has_next_page": True,
            "next_cursor": "next-page",
        }

    provider._get = get

    result = await provider._collect_pages(
        "/twitter/user/last_tweets",
        params={"userName": "elonmusk"},
        item_key="tweets",
        limit=20,
    )

    assert len(calls) == 1
    assert result["items"] == []
    assert result["next_cursor"] == "next-page"
    assert result["has_next_page"] is True


async def test_collect_pages_reads_nested_data_items() -> None:
    provider = object.__new__(XAPIIOProvider)
    provider.settings = XSettings(api_key="test-api-key")

    async def get(path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "data": {
                "tweets": [
                    {"id": "1"},
                    {"id": "2"},
                ],
            },
            "has_next_page": True,
            "next_cursor": "next-page",
        }

    provider._get = get

    result = await provider._collect_pages(
        "/twitter/user/last_tweets",
        params={"userName": "elonmusk"},
        item_key="tweets",
        limit=2,
    )

    assert result["items"] == [{"id": "1"}, {"id": "2"}]
    assert result["next_cursor"] == "next-page"
    assert result["has_next_page"] is True
