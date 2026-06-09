from collector.api.schemas import AccountsResponse, PostsResponse, RepliesResponse
from collector.services.ports import CollectionSource, QueryType


class CollectionService:
    def __init__(self, source: CollectionSource, max_posts_limit: int) -> None:
        self.source = source
        self.max_posts_limit = max_posts_limit

    async def get_account(self, usernames: list[str]):
        result = await self.source.get_accounts(usernames)
        return AccountsResponse(accounts=result.accounts, errors=result.errors, meta=result.metadata)

    async def search_accounts(self, query: str, limit: int) -> AccountsResponse:
        result = await self.source.search_accounts(query, limit=self._limit(limit))
        return AccountsResponse(accounts=result.accounts, errors=result.errors, meta=result.metadata)

    async def get_account_posts(
        self,
        username: str,
        limit: int,
        include_replies: bool,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostsResponse:
        posts_result = await self.source.get_account_posts(
            username,
            limit=self._limit(limit),
            include_replies=include_replies,
            since=since,
            until_date=until_date,
        )

        return PostsResponse(posts=posts_result.posts, meta=posts_result.metadata)
    
    async def posts_by_ids(self, ids: list[str]) -> PostsResponse:
        result = await self.source.get_posts_by_ids(ids)
        return PostsResponse(posts=result.posts, meta=result.metadata)

    async def search_posts(
        self,
        query: str,
        limit: int,
        query_type: QueryType,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostsResponse:
        result = await self.source.search_posts(
            query,
            limit=self._limit(limit),
            query_type=query_type,
            since=since,
            until_date=until_date,
        )
        return PostsResponse(posts=result.posts, meta=result.metadata)

    async def replies(self, post_id: str, limit: int) -> RepliesResponse:
        result = await self.source.get_replies(post_id, limit=self._limit(limit))
        return RepliesResponse(replies=result.replies, meta=result.metadata)

    def _limit(self, value: int) -> int:
        return max(1, min(value, self.max_posts_limit))
