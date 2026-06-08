from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Query

from collector.providers.factory import build_provider
from collector.services.collection import CollectionService


async def get_collection_service(
    provider_key: Annotated[str | None, Query()] = None,
) -> AsyncIterator[CollectionService]:
    provider = build_provider(provider_key)
    try:
        yield CollectionService(provider)
    finally:
        close = getattr(provider, "close", None)
        if close is not None:
            await close()
