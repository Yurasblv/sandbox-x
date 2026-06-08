from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Query

from collector.core.config import Settings, get_settings
from collector.providers.factory import build_provider
from collector.services.collection import CollectionService


async def get_collection_service(
    settings: Annotated[Settings, Depends(get_settings)],
    provider_key: Annotated[str | None, Query()] = None,
) -> AsyncIterator[CollectionService]:
    provider = build_provider(settings, provider_key)
    try:
        yield CollectionService(provider, settings)
    finally:
        close = getattr(provider, "close", None)
        if close is not None:
            await close()
