from abc import ABC, abstractmethod
from typing import Literal

from collector.models import ProviderMetadata, XAccount, XPost, XReply

QueryType = Literal["Latest", "Top"]


class AccountCollectionResult:
    def __init__(self, accounts: list[XAccount], metadata: ProviderMetadata) -> None:
        self.accounts = accounts
        self.metadata = metadata


class PostCollectionResult:
    def __init__(self, posts: list[XPost], metadata: ProviderMetadata) -> None:
        self.posts = posts
        self.metadata = metadata


class ReplyCollectionResult:
    def __init__(self, replies: list[XReply], metadata: ProviderMetadata) -> None:
        self.replies = replies
        self.metadata = metadata


class XProvider(ABC):
    @abstractmethod
    async def get_accounts(self, usernames: list[str]) -> AccountCollectionResult:
        raise NotImplementedError

    @abstractmethod
    async def search_accounts(self, query: str, *, limit: int) -> AccountCollectionResult:
        raise NotImplementedError

    @abstractmethod
    async def get_account_posts(
        self, username: str, *, limit: int, include_replies: bool
    ) -> PostCollectionResult:
        raise NotImplementedError

    @abstractmethod
    async def get_posts_by_ids(self, ids: list[str]) -> PostCollectionResult:
        raise NotImplementedError

    @abstractmethod
    async def search_posts(
        self, query: str, *, limit: int, query_type: QueryType
    ) -> PostCollectionResult:
        raise NotImplementedError

    @abstractmethod
    async def get_replies(self, post_id: str, *, limit: int) -> ReplyCollectionResult:
        raise NotImplementedError
