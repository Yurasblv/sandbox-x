from typing import Any

from collector.providers.x_api_io import XAPIIOProvider
from collector.providers.x_api_io_utils import map_account


def test_map_account_accepts_common_username_aliases() -> None:
    account = map_account({"id": "1", "screen_name": "openai", "name": "OpenAI"})

    assert account.username == "openai"


async def test_search_accounts_skips_invalid_user_items() -> None:
    provider = object.__new__(XAPIIOProvider)

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
