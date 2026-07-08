from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cow X"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    environment: str = "local"
    cors_allowed_origins: list[str] = Field(
        default=[
            "http://localhost:8081",
            "http://127.0.0.1:8081",
        ],
        validation_alias="CORS_ALLOWED_ORIGINS",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/cow_x",
        validation_alias="DATABASE_URL",
    )

    sarvam_api_key: str | None = Field(default=None, validation_alias="SARVAM_API_KEY")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.5", validation_alias="OPENAI_MODEL")
    openai_timeout_seconds: float = Field(
        default=30.0, validation_alias="OPENAI_TIMEOUT_SECONDS"
    )
    openai_max_retries: int = Field(default=2, validation_alias="OPENAI_MAX_RETRIES")

    twilio_account_sid: str | None = Field(
        default=None, validation_alias="TWILIO_ACCOUNT_SID"
    )
    twilio_auth_token: str | None = Field(
        default=None, validation_alias="TWILIO_AUTH_TOKEN"
    )
    twilio_verify_service_sid: str | None = Field(
        default=None, validation_alias="TWILIO_VERIFY_SERVICE_SID"
    )
    firebase_service_account_path: str | None = Field(
        default=None, validation_alias="FIREBASE_SERVICE_ACCOUNT_PATH"
    )
    firebase_service_account_json: str | None = Field(
        default=None, validation_alias="FIREBASE_SERVICE_ACCOUNT_JSON"
    )

    llm_provider: str = "openai"
    stt_provider: str = "sarvam"
    tts_provider: str = "sarvam"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def use_async_postgres_driver(cls, value: str) -> str:
        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql+asyncpg://", 1)
        elif value.startswith("postgresql://"):
            value = value.replace("postgresql://", "postgresql+asyncpg://", 1)

        if not value.startswith("postgresql+asyncpg://"):
            return value

        parts = urlsplit(value)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        ssl_mode = query.pop("sslmode", None)
        query.pop("channel_binding", None)
        if ssl_mode and "ssl" not in query:
            query["ssl"] = ssl_mode
        return urlunsplit(parts._replace(query=urlencode(query)))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
