from __future__ import annotations

from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PulseHR"
    app_env: str = "local"
    debug: bool = False
    api_prefix: str = ""

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "pulsehr"
    postgres_user: str = "pulsehr"
    postgres_password: str = "pulsehr_password"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    jwt_secret_key: str = Field(min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 30

    otp_ttl_seconds: int = 300
    otp_rate_limit_seconds: int = 60
    otp_max_verify_attempts: int = 5

    telegram_bot_token: str | None = None

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    email_from: str | None = None

    sms_provider_url: str | None = None
    sms_api_key: str | None = None
    sms_sender: str | None = None

    notification_step_delay_seconds: int = 900

    @cached_property
    def database_url(self) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @cached_property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
