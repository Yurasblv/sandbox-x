import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from loguru import logger

from collector.core.config import Settings
from collector.core.errors import (
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from collector.models import ProviderMetadata, XAccount, XPost, XReply
from collector.providers.base import (
    AccountCollectionResult,
    PostCollectionResult,
    QueryType,
    ReplyCollectionResult,
    TwitterProvider,
)


class TwitterAPIIOProvider(TwitterProvider):
    key = "twitterapi_io"

    def __init__(self, settings: Settings) -> None:
        if not settings.twitterapi_io_api_key:
            raise ProviderConfigurationError("TWITTERAPI_IO_API_KEY is required")

        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url=settings.twitterapi_io_base_url.rstrip("/"),
            headers={"X-API-Key": settings.twitterapi_io_api_key},
            timeout=settings.http_timeout_seconds,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def get_accounts(self, usernames: list[str]) -> AccountCollectionResult:
        accounts: list[XAccount] = []
        raw: dict[str, Any] = {}
        for username in usernames:
            payload = await self._get("/twitter/user/info", params={"userName": username})
            raw[username] = payload
            user = payload.get("data") or payload.get("user") or payload
            accounts.append(_map_account(user))

        return AccountCollectionResult(
            accounts,
            ProviderMetadata(
                provider_key=self.key,
                request_path="/twitter/user/info",
                input_ids=usernames,
                raw=raw,
            ),
        )

    async def search_accounts(self, query: str, *, limit: int) -> AccountCollectionResult:
        payload = await self._collect_pages(
            "/twitter/user/search",
            params={"query": query},
            item_key="users",
            limit=limit,
        )
        accounts = [_map_account(item) for item in payload["items"]]
        return AccountCollectionResult(
            accounts,
            ProviderMetadata(
                provider_key=self.key,
                request_path="/twitter/user/search",
                input_query=query,
                next_cursor=payload["next_cursor"],
                has_next_page=payload["has_next_page"],
                raw={"pages": payload["pages"]},
            ),
        )

    async def get_account_posts(
        self, username: str, *, limit: int, include_replies: bool
    ) -> PostCollectionResult:
        payload = await self._collect_pages(
            "/twitter/user/last_tweets",
            params={"userName": username, "includeReplies": str(include_replies).lower()},
            item_key="tweets",
            limit=limit,
        )
        posts = [_map_post(item) for item in payload["items"]]
        return PostCollectionResult(
            posts,
            ProviderMetadata(
                provider_key=self.key,
                request_path="/twitter/user/last_tweets",
                input_ids=[username],
                next_cursor=payload["next_cursor"],
                has_next_page=payload["has_next_page"],
                raw={"pages": payload["pages"]},
            ),
        )

    async def get_posts_by_ids(self, ids: list[str]) -> PostCollectionResult:
        payload = await self._get("/twitter/tweets", params={"tweet_ids": ",".join(ids)})
        raw_items = payload.get("tweets") or payload.get("data") or []
        if isinstance(raw_items, dict):
            raw_items = list(raw_items.values())
        posts = [_map_post(item) for item in raw_items]
        return PostCollectionResult(
            posts,
            ProviderMetadata(
                provider_key=self.key,
                request_path="/twitter/tweets",
                input_ids=ids,
                raw=payload,
            ),
        )

    async def search_posts(
        self, query: str, *, limit: int, query_type: QueryType
    ) -> PostCollectionResult:
        payload = await self._collect_pages(
            "/twitter/tweet/advanced_search",
            params={"query": query, "queryType": query_type},
            item_key="tweets",
            limit=limit,
        )
        posts = [_map_post(item) for item in payload["items"]]
        return PostCollectionResult(
            posts,
            ProviderMetadata(
                provider_key=self.key,
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
            params={"tweetId": post_id},
            item_key="replies",
            limit=limit,
        )
        replies = [_map_reply(item) for item in payload["items"]]
        return ReplyCollectionResult(
            replies,
            ProviderMetadata(
                provider_key=self.key,
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
            logger.bind(
                provider=self.key,
                path=path,
                cursor=cursor or None,
                collected_count=len(items),
                limit=limit,
            ).info("provider_page_requested")
            page = await self._get(path, params=page_params)
            pages.append(page)
            items.extend(page.get(item_key) or [])
            has_next_page = bool(page.get("has_next_page"))
            cursor = page.get("next_cursor") or ""
            logger.bind(
                provider=self.key,
                path=path,
                page_item_count=len(page.get(item_key) or []),
                collected_count=len(items),
                has_next_page=has_next_page,
                next_cursor=cursor or None,
            ).info("provider_page_received")
            if not cursor:
                break

        return {
            "items": items[:limit],
            "pages": pages,
            "next_cursor": cursor or None,
            "has_next_page": has_next_page,
        }

    async def _get(self, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        async def send() -> httpx.Response:
            started_at = time.perf_counter()
            logger.bind(
                provider=self.key,
                method="GET",
                path=path,
                params=_redact(params),
            ).info("provider_request_started")
            response = await self.client.get(path, params=params)
            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.bind(
                provider=self.key,
                method="GET",
                path=path,
                params=_redact(params),
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
                response_preview=response.text[:500],
            ).info("provider_response_received")
            return response

        response = await self._retry(send)
        if response.status_code == 429:
            logger.bind(provider=self.key, path=path, params=_redact(params)).warning(
                "provider_rate_limit"
            )
            raise ProviderRateLimitError("TwitterAPI.io rate limit reached")
        if response.is_error:
            logger.bind(
                provider=self.key,
                path=path,
                params=_redact(params),
                status_code=response.status_code,
                response_preview=response.text[:1000],
            ).error("provider_request_error")
            raise ProviderRequestError(
                "TwitterAPI.io request failed",
                details={"status_code": response.status_code, "body": response.text[:1000]},
            )

        payload = response.json()
        if payload.get("status") == "error":
            logger.bind(
                provider=self.key,
                path=path,
                params=_redact(params),
                provider_message=payload.get("msg") or payload.get("message"),
            ).error("provider_payload_error")
            raise ProviderRequestError(
                payload.get("msg") or payload.get("message") or "TwitterAPI.io returned an error",
                details={"payload": payload},
            )
        return payload

    async def _retry(self, call: Callable[[], Awaitable[httpx.Response]]) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(1, self.settings.http_max_retries + 1):
            try:
                response = await call()
                if response.status_code != 429 and response.status_code < 500:
                    return response
                retry_after = _retry_after_seconds(response)
                sleep_seconds = retry_after or self.settings.http_backoff_seconds * attempt
                logger.bind(
                    provider=self.key,
                    attempt=attempt,
                    status_code=response.status_code,
                    sleep_seconds=sleep_seconds,
                ).warning("provider_request_retry")
                await asyncio.sleep(sleep_seconds)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                if attempt == self.settings.http_max_retries:
                    break
                sleep_seconds = self.settings.http_backoff_seconds * attempt
                logger.bind(
                    provider=self.key,
                    attempt=attempt,
                    error=str(exc),
                    sleep_seconds=sleep_seconds,
                ).warning("provider_transport_retry")
                await asyncio.sleep(sleep_seconds)

        if last_error is not None:
            logger.bind(provider=self.key, error=str(last_error)).error("provider_transport_error")
            raise ProviderRequestError(
                "TwitterAPI.io transport error",
                details={"error": str(last_error)},
            )
        return response


def _map_account(raw: dict[str, Any]) -> XAccount:
    return XAccount.model_validate({**raw, "raw": raw})


def _map_post(raw: dict[str, Any]) -> XPost:
    mapped = {**raw, "raw": raw}
    if author := raw.get("author"):
        mapped["author"] = _map_account(author)
    mapped["media"] = raw.get("media") or raw.get("extendedEntities", {}).get("media") or []
    return XPost.model_validate(mapped)


def _map_reply(raw: dict[str, Any]) -> XReply:
    return XReply.model_validate(_map_post(raw).model_dump())


def _retry_after_seconds(response: httpx.Response) -> float | None:
    value = response.headers.get("retry-after")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _redact(params: dict[str, Any]) -> dict[str, Any]:
    return {key: ("***" if "key" in key.lower() else value) for key, value in params.items()}
