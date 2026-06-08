from collector.core.config import settings
from collector.core.enums import ProviderKey
from collector.core.errors import ProviderNotFoundError
from collector.providers.base import XProvider
from collector.providers.x_api_io import XAPIIOProvider


def build_provider(provider_key: str | None = None) -> XProvider:
    raw_key = provider_key or settings.x.provider
    try:
        key = ProviderKey(raw_key)
    except ValueError as exc:
        raise ProviderNotFoundError(
            f"Unsupported provider: {raw_key}",
            details={"provider_key": raw_key},
        ) from exc

    if key == ProviderKey.X_IO:
        return XAPIIOProvider()
    raise ProviderNotFoundError(f"Unsupported provider: {key}", details={"provider_key": key})
