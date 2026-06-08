from collector.core.config import Settings
from collector.core.errors import ProviderNotFoundError
from collector.providers.base import TwitterProvider
from collector.providers.twitterapi_io import TwitterAPIIOProvider


def build_provider(settings: Settings, provider_key: str | None = None) -> TwitterProvider:
    key = provider_key or settings.twitter_provider
    if key == TwitterAPIIOProvider.key:
        return TwitterAPIIOProvider(settings)
    raise ProviderNotFoundError(f"Unsupported provider: {key}", details={"provider_key": key})
