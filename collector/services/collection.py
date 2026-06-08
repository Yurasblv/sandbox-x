from collector.core.config import Settings
from collector.core.config import settings as app_settings
from collector.providers.base import QueryType, XProvider

DEFAULT_ACCOUNT_USERNAMES = ["elonmusk", "realDonaldTrump"]


class CollectionService:
    settings: Settings = app_settings

    def __init__(self, provider: XProvider) -> None:
        self.provider = provider

    async def default_accounts(self):
        return await self.provider.get_accounts(DEFAULT_ACCOUNT_USERNAMES)

    async def accounts(self, usernames: list[str]):
        return await self.provider.get_accounts(usernames)

    async def search_accounts(self, query: str, limit: int):
        return await self.provider.search_accounts(query, limit=self._limit(limit))

    async def account_posts_with_replies(self, username: str, limit: int, replies_limit: int):
        posts_result = await self.provider.get_account_posts(
            username,
            limit=self._limit(limit),
            include_replies=True,
        )
        replies_by_post: dict[str, object] = {}
        for post in posts_result.posts:
            replies_by_post[post.id] = await self.provider.get_replies(
                post.id,
                limit=self._limit(replies_limit),
            )
        return posts_result, replies_by_post

    async def posts_by_ids(self, ids: list[str]):
        return await self.provider.get_posts_by_ids(ids)

    async def search_posts(self, query: str, limit: int, query_type: QueryType):
        return await self.provider.search_posts(
            query,
            limit=self._limit(limit),
            query_type=query_type,
        )

    async def replies(self, post_id: str, limit: int):
        return await self.provider.get_replies(post_id, limit=self._limit(limit))

    def _limit(self, value: int) -> int:
        return max(1, min(value, self.settings.x.max_page_limit))
