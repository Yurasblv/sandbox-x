from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from aiolimiter import AsyncLimiter
from fastapi import Depends, Query

from collector.core.config import BaseProviderSettings, CollectorSettings, Settings, settings
from collector.core.enums import ProviderKey
from collector.core.errors import ProviderNotFoundError
from collector.providers.factory import build_provider
from collector.services.collection import CollectionService


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


def get_collector_settings(
    app_settings: Annotated[Settings, Depends(get_settings)],
) -> CollectorSettings:
    return app_settings.collector


@lru_cache
def build_provider_rate_limiter(requests: int, period_seconds: float) -> AsyncLimiter:
    return AsyncLimiter(max(1, requests), time_period=max(period_seconds, 1.0))


def get_provider_rate_limiter(
    collector_settings: Annotated[CollectorSettings, Depends(get_collector_settings)],
) -> AsyncLimiter:
    return build_provider_rate_limiter(
        collector_settings.rate_limit_requests,
        collector_settings.rate_limit_period_seconds,
    )


async def get_collection_service(
    provider_settings: Annotated[BaseProviderSettings, Depends(get_provider_settings)],
    collector_settings: Annotated[CollectorSettings, Depends(get_collector_settings)],
    rate_limiter: Annotated[AsyncLimiter, Depends(get_provider_rate_limiter)],
) -> AsyncIterator[CollectionService]:
    provider = build_provider(provider_settings, collector_settings, rate_limiter)

    try:
        yield CollectionService(provider, collector_settings)

    finally:
        if close := getattr(provider, "close", None):
            await close()
