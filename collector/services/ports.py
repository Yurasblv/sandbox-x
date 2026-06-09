from typing import Literal, Protocol

from collector.models import ErrorDTO, ProviderMetadata, XAccount, XPost, XReply

QueryType = Literal["Latest", "Top"]


class AccountCollectionResult:
    def __init__(
        self,
        accounts: list[XAccount],
        metadata: ProviderMetadata,
        errors: list[ErrorDTO] | None = None,
    ) -> None:
        self.accounts = accounts
        self.metadata = metadata
        self.errors = errors or []


class PostCollectionResult:
    def __init__(self, posts: list[XPost], metadata: ProviderMetadata) -> None:
        self.posts = posts
        self.metadata = metadata


class ReplyCollectionResult:
    def __init__(self, replies: list[XReply], metadata: ProviderMetadata) -> None:
        self.replies = replies
        self.metadata = metadata


class CollectionSource(Protocol):
    async def get_accounts(self, usernames: list[str]) -> AccountCollectionResult: ...

    async def search_accounts(self, query: str, *, limit: int) -> AccountCollectionResult: ...

    async def get_account_posts(
        self,
        username: str,
        *,
        limit: int,
        include_replies: bool,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostCollectionResult: ...

    async def get_posts_by_ids(self, ids: list[str]) -> PostCollectionResult: ...

    async def search_posts(
        self,
        query: str,
        *,
        limit: int,
        query_type: QueryType,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostCollectionResult: ...

    async def get_replies(self, post_id: str, *, limit: int) -> ReplyCollectionResult: ...
