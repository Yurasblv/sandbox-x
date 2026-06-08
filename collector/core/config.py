from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "twitter-collector-service"
    environment: str = "local"
    log_level: str = "INFO"

    twitter_provider: str = "twitterapi_io"
    twitterapi_io_base_url: str = "https://api.twitterapi.io"
    twitterapi_io_api_key: str = Field(default="", repr=False)

    http_timeout_seconds: float = 30.0
    http_max_retries: int = 3
    http_backoff_seconds: float = 1.0
    default_page_limit: int = 20
    max_page_limit: int = 200

    default_account_usernames: list[str] = ["elonmusk", "realDonaldTrump"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
