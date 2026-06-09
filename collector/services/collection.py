from collector.api.schemas import AccountsResponse, PostsResponse, RepliesResponse
from collector.core.config import CollectorSettings
from collector.providers.base import QueryType, XProvider


class CollectionService:
    def __init__(self, provider: XProvider, settings: CollectorSettings) -> None:
        self.provider = provider
        self.settings = settings

    async def get_account(self, usernames: list[str]):
        result = await self.provider.get_accounts(usernames)
        return AccountsResponse(accounts=result.accounts, errors=result.errors, meta=result.metadata)

    async def search_accounts(self, query: str, limit: int) -> AccountsResponse:
        result = await self.provider.search_accounts(query, limit=self._limit(limit))
        return AccountsResponse(accounts=result.accounts, errors=result.errors, meta=result.metadata)

    async def get_account_posts(
        self,
        username: str,
        limit: int,
        include_replies: bool,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostsResponse:
        posts_result = await self.provider.get_account_posts(
            username,
            limit=self._limit(limit),
            include_replies=include_replies,
            since=since,
            until_date=until_date,
        )

        return PostsResponse(posts=posts_result.posts, meta=posts_result.metadata)
    
    async def posts_by_ids(self, ids: list[str]) -> PostsResponse:
        result = await self.provider.get_posts_by_ids(ids)
        return PostsResponse(posts=result.posts, meta=result.metadata)

    async def search_posts(
        self,
        query: str,
        limit: int,
        query_type: QueryType,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostsResponse:
        result = await self.provider.search_posts(
            query,
            limit=self._limit(limit),
            query_type=query_type,
            since=since,
            until_date=until_date,
        )
        return PostsResponse(posts=result.posts, meta=result.metadata)

    async def replies(self, post_id: str, limit: int) -> RepliesResponse:
        result = await self.provider.get_replies(post_id, limit=self._limit(limit))
        return RepliesResponse(replies=result.replies, meta=result.metadata)

    def _limit(self, value: int) -> int:
        return max(1, min(value, self.settings.max_posts_limit))
