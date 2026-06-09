from abc import ABC, abstractmethod

from collector.services.ports import (
    AccountCollectionResult,
    CollectionSource,
    PostCollectionResult,
    QueryType,
    ReplyCollectionResult,
)


class XProvider(CollectionSource, ABC):
    @abstractmethod
    async def get_accounts(self, usernames: list[str]) -> AccountCollectionResult:
        raise NotImplementedError

    @abstractmethod
    async def search_accounts(self, query: str, *, limit: int) -> AccountCollectionResult:
        raise NotImplementedError

    @abstractmethod
    async def get_account_posts(
        self,
        username: str,
        *,
        limit: int,
        include_replies: bool,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostCollectionResult:
        raise NotImplementedError

    @abstractmethod
    async def get_posts_by_ids(self, ids: list[str]) -> PostCollectionResult:
        raise NotImplementedError

    @abstractmethod
    async def search_posts(
        self,
        query: str,
        *,
        limit: int,
        query_type: QueryType,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostCollectionResult:
        raise NotImplementedError

    @abstractmethod
    async def get_replies(self, post_id: str, *, limit: int) -> ReplyCollectionResult:
        raise NotImplementedError
