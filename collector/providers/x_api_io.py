import asyncio
from typing import Any

import httpx
from aiolimiter import AsyncLimiter
from httpx_retries import Retry, RetryTransport
from loguru import logger

from collector.core.config import XSettings
from collector.core.errors import (
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from collector.models import ErrorDTO, XAccount
from collector.providers.base import (
    AccountCollectionResult,
    PostCollectionResult,
    QueryType,
    ReplyCollectionResult,
    XProvider,
)
from collector.providers.x_api_io_utils import (
    build_metadata,
    build_params,
    map_account,
    map_post,
    map_reply,
)


class XAPIIOProvider(XProvider):
    @property
    def provider_key(self) -> str:
        return self.settings.provider.value

    def __init__(self, settings: XSettings, request_batch_size: int, rate_limiter: AsyncLimiter) -> None:
        self.settings = settings
        self.request_batch_size = request_batch_size
        self.rate_limiter = rate_limiter
        if not self.settings.api_key:
            raise ProviderConfigurationError("X__API_KEY is required")

        retry = Retry(
            total=max(self.settings.max_retries - 1, 0),
            backoff_factor=self.settings.backoff_seconds,
            status_forcelist=(429, *range(500, 600)),
            retry_on_exceptions=(httpx.TimeoutException, httpx.TransportError),
        )
        self.client = httpx.AsyncClient(
            base_url=self.settings.base_url.rstrip("/"),
            headers={"X-API-Key": self.settings.api_key},
            timeout=self.settings.timeout_seconds,
            transport=RetryTransport(retry=retry),
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def get_accounts(self, usernames: list[str]) -> AccountCollectionResult:
        accounts: list[XAccount] = []
        errors: list[ErrorDTO] = []
        raw: dict[str, Any] = {}

        for i in range(0, len(usernames), self.request_batch_size):
            batch = usernames[i : i + self.request_batch_size]
            batch_payloads = await asyncio.gather(
                *(self._get_account_payload(username) for username in batch),
                return_exceptions=True,
            )

            for username, payload in zip(batch, batch_payloads, strict=True):

                if isinstance(payload, Exception):
                    errors.append(_account_error(username, payload))
                    continue

                raw[username] = payload
                user = payload.get("data") or payload.get("user") or payload
                accounts.append(map_account(user))

        return AccountCollectionResult(
            accounts,
            build_metadata(
                provider_key=self.provider_key,
                request_path="/twitter/user/info",
                input_ids=usernames,
                raw=raw,
            ),
            errors=errors,
        )

    async def _get_account_payload(
        self,
        username: str,
    ) -> dict[str, Any]:
        return await self._get(
            "/twitter/user/info",
            params=build_params(userName=username),
        )

    async def search_accounts(self, query: str, *, limit: int) -> AccountCollectionResult:
        payload = await self._collect_pages(
            "/twitter/user/search",
            params=build_params(query=query),
            item_key="users",
            limit=limit,
        )
        accounts: list[XAccount] = []
        errors: list[ErrorDTO] = []
        for index, item in enumerate(payload["items"]):

            try:
                accounts.append(map_account(item))

            except Exception as exc:
                source = _account_error_source(item, index)
                logger.warning(
                    "provider_account_mapping_error provider={} path={} source={} error={}",
                    self.provider_key,
                    "/twitter/user/search",
                    source,
                    str(exc),
                )
                errors.append(ErrorDTO(source=source, error=str(exc), status_code=502))

        return AccountCollectionResult(
            accounts,
            build_metadata(
                provider_key=self.provider_key,
                request_path="/twitter/user/search",
                input_query=query,
                next_cursor=payload["next_cursor"],
                has_next_page=payload["has_next_page"],
                raw={"pages": payload["pages"]},
            ),
            errors=errors,
        )

    async def get_account_posts(
        self,
        username: str,
        *,
        limit: int,
        include_replies: bool,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostCollectionResult:
        payload = await self._collect_pages(
            "/twitter/user/last_tweets",
            params=build_params(
                userName=username,
                includeReplies=str(include_replies).lower(),
                since=since,
                until_date=until_date,
            ),
            item_key="tweets",
            limit=limit,
        )
        posts = [map_post(item) for item in payload["items"]]
        return PostCollectionResult(
            posts,
            build_metadata(
                provider_key=self.provider_key,
                request_path="/twitter/user/last_tweets",
                input_ids=[username],
                next_cursor=payload["next_cursor"],
                has_next_page=payload["has_next_page"],
                raw={"pages": payload["pages"]},
            ),
        )

    async def get_posts_by_ids(self, ids: list[str]) -> PostCollectionResult:
        payload = await self._get(
            "/twitter/tweets",
            params=build_params(tweet_ids=",".join(ids)),
        )
        raw_items = payload.get("tweets") or payload.get("data") or []
        if isinstance(raw_items, dict):
            raw_items = list(raw_items.values())
        posts = [map_post(item) for item in raw_items]
        return PostCollectionResult(
            posts,
            build_metadata(
                provider_key=self.provider_key,
                request_path="/twitter/tweets",
                input_ids=ids,
                raw=payload,
            ),
        )

    async def search_posts(
        self,
        query: str,
        *,
        limit: int,
        query_type: QueryType,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostCollectionResult:
        payload = await self._collect_pages(
            "/twitter/tweet/advanced_search",
            params=build_params(
                query=query,
                queryType=query_type,
                since=since,
                until_date=until_date,
            ),
            item_key="tweets",
            limit=limit,
        )
        posts = [map_post(item) for item in payload["items"]]
        return PostCollectionResult(
            posts,
            build_metadata(
                provider_key=self.provider_key,
                request_path="/twitter/tweet/advanced_search",
                input_query=query,
                next_cursor=payload["next_cursor"],
                has_next_page=payload["has_next_page"],
                raw={"pages": payload["pages"]},
            ),
        )

    async def get_replies(self, post_id: str, *, limit: int) -> ReplyCollectionResult:
        payload = await self._collect_pages(
            "/twitter/tweet/replies",
            params=build_params(tweetId=post_id),
            item_key="replies",
            limit=limit,
        )
        replies = [map_reply(item) for item in payload["items"]]
        return ReplyCollectionResult(
            replies,
            build_metadata(
                provider_key=self.provider_key,
                request_path="/twitter/tweet/replies",
                input_ids=[post_id],
                next_cursor=payload["next_cursor"],
                has_next_page=payload["has_next_page"],
                raw={"pages": payload["pages"]},
            ),
        )

    async def _collect_pages(
        self,
        path: str,
        *,
        params: dict[str, Any],
        item_key: str,
        limit: int,
    ) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        pages: list[dict[str, Any]] = []
        cursor = ""
        has_next_page = True

        while len(items) < limit and has_next_page:
            page_params = {**params, "cursor": cursor}
            logger.info(
                "provider_page_requested provider={} path={} cursor={} collected={} limit={}",
                self.provider_key,
                path,
                cursor,
                len(items),
                limit,
            )

            page = await self._get(path, params=page_params)
            pages.append(page)
            page_items = _page_items(page, item_key)
            items.extend(page_items)
            has_next_page = bool(page.get("has_next_page"))
            cursor = page.get("next_cursor") or ""

            logger.info(
                "provider_page_received provider={} path={} status=ok collected={} has_next_page={} next_cursor={}",
                self.provider_key,
                path,
                len(items),
                has_next_page,
                cursor or None,
            )

            if not page_items:
                logger.info(
                    "provider_pagination_stopped provider={} path={} reason=empty_page collected={} next_cursor={}",
                    self.provider_key,
                    path,
                    len(items),
                    cursor or None,
                )
                break

            if not cursor:
                break

        return {
            "items": items[:limit],
            "pages": pages,
            "next_cursor": cursor or None,
            "has_next_page": has_next_page,
        }

    async def _get(self, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        async with self.rate_limiter:
            response = await self.send_request("GET", path, params=params)

        if response.status_code == 429:
            logger.warning(
                "provider_rate_limit provider={} path={} status_code={}",
                self.provider_key,
                path,
                response.status_code,
            )

            raise ProviderRateLimitError(
                f"X API provider rate limit reached (status_code={response.status_code})",
                details={"status_code": response.status_code, "body": response.text[:250]},
            )

        if response.is_error:
            logger.error(
                "provider_request_error provider={} path={} status_code={}",
                self.provider_key,
                path,
                response.status_code,
            )

            raise ProviderRequestError(
                f"X API provider request failed (status_code={response.status_code})",
                details={"status_code": response.status_code, "body": response.text[:250]},
            )

        payload = response.json()
        if payload.get("status") == "error":
            logger.error(
                "provider_payload_error provider={} path={} status_code={} provider_message={}",
                self.provider_key,
                path,
                response.status_code,
                payload.get("msg") or payload.get("message"),
            )
            raise ProviderRequestError(
                (
                    f"{payload.get('msg') or payload.get('message') or 'X API provider returned an error'} "
                    f"(status_code={response.status_code})"
                ),
                details={"payload": payload},
            )
        return payload

    async def send_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any],
    ) -> httpx.Response:
        return await self.client.request(method, path, params=params)


def _account_error(username: str, exc: Exception) -> ErrorDTO:
    status_code = 500
    if isinstance(exc, ProviderRateLimitError):
        status_code = 429
    elif isinstance(exc, ProviderRequestError):
        status_code = int((exc.details or {}).get("status_code") or 500)

    return ErrorDTO(source=username, error=str(exc), status_code=status_code)


def _page_items(page: dict[str, Any], item_key: str) -> list[dict[str, Any]]:
    raw_items = page.get(item_key)
    if raw_items is None and isinstance(page.get("data"), dict):
        raw_items = page["data"].get(item_key)
    return raw_items or []


def _account_error_source(item: Any, index: int) -> str:
    if isinstance(item, dict):
        source = (
            item.get("userName")
            or item.get("username")
            or item.get("screen_name")
            or item.get("screenName")
            or item.get("user_name")
            or item.get("id")
        )
        if source:
            return str(source)
    return f"users[{index}]"
