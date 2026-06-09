from collector.core.config import XSettings, settings
from collector.core.enums import ProviderKey

PROVIDER_SETTINGS: dict[ProviderKey, XSettings] = {
    ProviderKey.X_IO: settings.x,
}


def get_provider_settings(provider_key: ProviderKey | str) -> XSettings:
    key = ProviderKey(provider_key)
    provider_settings = PROVIDER_SETTINGS.get(key)
    if provider_settings is None:
        raise ValueError(f"Unsupported provider: {provider_key}")
    return provider_settings
