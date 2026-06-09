from aiolimiter import AsyncLimiter

from collector.core.config import BaseProviderSettings
from collector.core.enums import ProviderKey
from collector.core.errors import ProviderNotFoundError
from collector.providers.x_api_io import XAPIIOProvider
from collector.services.ports import CollectionSource


def build_provider(
    provider_settings: BaseProviderSettings,
    request_batch_size: int,
    rate_limiter: AsyncLimiter,
) -> CollectionSource:
    key = provider_settings.provider

    if key == ProviderKey.X_IO:
        return XAPIIOProvider(provider_settings, request_batch_size, rate_limiter)

    raise ProviderNotFoundError(f"Unsupported provider: {key}", details={"provider_key": key})
