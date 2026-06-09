from aiolimiter import AsyncLimiter

from collector.core.config import BaseProviderSettings, CollectorSettings
from collector.core.enums import ProviderKey
from collector.core.errors import ProviderNotFoundError
from collector.providers.base import XProvider
from collector.providers.x_api_io import XAPIIOProvider


def build_provider(
    provider_settings: BaseProviderSettings,
    collector_settings: CollectorSettings,
    rate_limiter: AsyncLimiter,
) -> XProvider:
    key = provider_settings.provider

    if key == ProviderKey.X_IO:
        return XAPIIOProvider(provider_settings, collector_settings.request_batch_size, rate_limiter)

    raise ProviderNotFoundError(f"Unsupported provider: {key}", details={"provider_key": key})
