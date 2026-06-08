import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from loguru import logger

from collector.core.errors import ProviderRequestError


def retry_provider_request(
    call: Callable[..., Awaitable[httpx.Response]],
) -> Callable[..., Awaitable[httpx.Response]]:
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> httpx.Response:
        provider_settings = self.settings.x
        last_error: Exception | None = None

        for attempt in range(1, provider_settings.max_retries + 1):
            try:
                response = await call(self, *args, **kwargs)
                if response.status_code != 429 and response.status_code < 500:
                    return response

                retry_after = _retry_after_seconds(response)
                sleep_seconds = retry_after or provider_settings.backoff_seconds * attempt
                logger.bind(
                    provider=self.provider_key,
                    attempt=attempt,
                    status_code=response.status_code,
                    sleep_seconds=sleep_seconds,
                ).warning("provider_request_retry")
                await asyncio.sleep(sleep_seconds)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                if attempt == provider_settings.max_retries:
                    break

                sleep_seconds = provider_settings.backoff_seconds * attempt
                logger.bind(
                    provider=self.provider_key,
                    attempt=attempt,
                    error=str(exc),
                    sleep_seconds=sleep_seconds,
                ).warning("provider_transport_retry")
                await asyncio.sleep(sleep_seconds)

        if last_error is not None:
            logger.bind(provider=self.provider_key, error=str(last_error)).error(
                "provider_transport_error"
            )
            raise ProviderRequestError(
                "Provider transport error",
                details={"error": str(last_error)},
            )
        return response

    return wrapper


def _retry_after_seconds(response: httpx.Response) -> float | None:
    value = response.headers.get("retry-after")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
