from collector.api.schemas import AccountsResponse, PostsResponse, PostsWithRepliesResponse, RepliesResponse
from collector.providers.base import QueryType, XProvider
from collector.services.utils import get_provider_settings


class CollectionService:
    def __init__(self, provider: XProvider) -> None:
        self.provider = provider
        self.settings = get_provider_settings(provider.provider_key)

    async def get_account(self, usernames: list[str]):
        result = await self.provider.get_accounts(usernames)
        return AccountsResponse(accounts=result.accounts, errors=result.errors, meta=result.metadata)

    async def search_accounts(self, query: str, limit: int) -> AccountsResponse:
        result = await self.provider.search_accounts(query, limit=self._limit(limit))
        return AccountsResponse(accounts=result.accounts, errors=result.errors, meta=result.metadata)

    async def get_account_posts(
        self,
        username: str,
        posts_limit: int,
        replies_limit: int,
        since: str | None = None,
        until_date: str | None = None,
    ):
        posts_result = await self.provider.get_account_posts(
            username,
            limit=self._limit(posts_limit),
            include_replies=True,
            since=since,
            until_date=until_date,
        )
        replies_by_post: dict[str, object] = {}

        if replies_limit > 0:
            for post in posts_result.posts:
                replies_by_post[post.id] = await self.provider.get_replies(
                    post.id,
                    limit=self._limit(replies_limit),
                )

        return PostsWithRepliesResponse(
            posts=posts_result.posts,
            replies_by_post={
                post_id: reply_result.replies for post_id, reply_result in replies_by_post.items()
            },
            meta=posts_result.metadata,
            replies_meta={
                post_id: reply_result.metadata for post_id, reply_result in replies_by_post.items()
            },
        )
    
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
