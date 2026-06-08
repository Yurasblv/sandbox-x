from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from collector.core.enums import ProviderKey


class AppSettings(BaseModel):
    app_name: str = "x-collector-service"
    environment: str = "local"
    log_level: str = "INFO"

    cors_allow_origins: list[str] = ["*"]
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]


class XSettings(BaseModel):
    provider: ProviderKey = ProviderKey.X_IO
    default_page_limit: int = 20
    max_page_limit: int = 200

    base_url: str = "https://api.twitterapi.io"
    api_key: str = Field(default="", repr=False)

    timeout_seconds: float = 30.0
    max_retries: int = 3
    backoff_seconds: float = 1.0


class Settings(BaseSettings):
    app: AppSettings = Field(default_factory=AppSettings)
    x: XSettings = Field(default_factory=XSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()
