from collections.abc import AsyncIterator
from typing import Annotated

from aiolimiter import AsyncLimiter
from fastapi import Depends, Query

from collector.core.config import BaseProviderSettings, Settings, settings
from collector.core.enums import ProviderKey
from collector.core.errors import ProviderNotFoundError
from collector.providers.factory import build_provider
from collector.services.collection import CollectionService

PROVIDER_RATE_LIMITER = AsyncLimiter(
    max(1, settings.collector.rate_limit_requests),
    time_period=max(settings.collector.rate_limit_period_seconds, 1.0),
)


def get_settings() -> Settings:
    return settings


def get_provider_key(
    app_settings: Annotated[Settings, Depends(get_settings)],
    provider_key: Annotated[ProviderKey | None, Query()] = None,
) -> ProviderKey:
    if provider_key:
        return provider_key

    if app_settings.x.provider:
        return app_settings.x.provider

    raise ProviderNotFoundError("Provider is not configured", details={"provider_key": None})


def get_provider_settings(
    provider_key: Annotated[ProviderKey, Depends(get_provider_key)],
    app_settings: Annotated[Settings, Depends(get_settings)],
) -> BaseProviderSettings:
    if provider_key == ProviderKey.X_IO:
        return app_settings.x

    raise ProviderNotFoundError(
        f"Unsupported provider: {provider_key}",
        details={"provider_key": provider_key},
    )


def get_max_posts_limit(
    app_settings: Annotated[Settings, Depends(get_settings)],
) -> int:
    return app_settings.collector.max_posts_limit


def get_request_batch_size(
    app_settings: Annotated[Settings, Depends(get_settings)],
) -> int:
    return app_settings.collector.request_batch_size


def get_provider_rate_limiter() -> AsyncLimiter:
    return PROVIDER_RATE_LIMITER


async def get_collection_service(
    provider_settings: Annotated[BaseProviderSettings, Depends(get_provider_settings)],
    max_posts_limit: Annotated[int, Depends(get_max_posts_limit)],
    request_batch_size: Annotated[int, Depends(get_request_batch_size)],
    rate_limiter: Annotated[AsyncLimiter, Depends(get_provider_rate_limiter)],
) -> AsyncIterator[CollectionService]:
    provider = build_provider(provider_settings, request_batch_size, rate_limiter)

    try:
        yield CollectionService(provider, max_posts_limit)
    finally:
        if close := getattr(provider, "close", None):
            await close()
