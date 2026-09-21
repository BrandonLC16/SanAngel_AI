import re
from functools import lru_cache
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

CorsOrigins = Annotated[tuple[str, ...], NoDecode]
DEFAULT_GREEN_API_URL = "https://api.green-api.com"


class HttpSettings(BaseSettings):
    """Non-secret HTTP configuration that is safe to load when the app starts."""

    app_env: Literal["development", "testing", "production"] = "development"
    app_name: str = Field(default="Carniceria AI Chatbot", min_length=1, max_length=100)
    app_host: str = Field(default="127.0.0.1", min_length=1, max_length=255)
    app_port: int = Field(default=8000, ge=1, le=65535)
    cors_allowed_origins: CorsOrigins = ()
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
        frozen=True,
        hide_input_in_errors=True,
        validate_default=True,
    )

    @field_validator("app_name", "app_host")
    @classmethod
    def normalize_non_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be blank")
        return normalized

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(origin.strip() for origin in value.split(",") if origin.strip())
        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_allowed_origins(cls, origins: tuple[str, ...]) -> tuple[str, ...]:
        normalized_origins: list[str] = []

        for origin in origins:
            normalized_origin = origin.strip().rstrip("/")
            parsed_origin = urlsplit(normalized_origin)

            try:
                parsed_origin.port
            except ValueError as exc:
                raise ValueError("CORS origins must use a valid port") from exc

            if origin.strip() == "*":
                raise ValueError("CORS wildcard origins are not allowed")
            if (
                parsed_origin.scheme not in {"http", "https"}
                or not parsed_origin.hostname
                or parsed_origin.username is not None
                or parsed_origin.password is not None
                or parsed_origin.path
                or parsed_origin.query
                or parsed_origin.fragment
            ):
                raise ValueError("CORS origins must contain only scheme, host, and optional port")
            if normalized_origin in normalized_origins:
                raise ValueError("CORS origins must not contain duplicates")

            normalized_origins.append(normalized_origin)

        return tuple(normalized_origins)


class Settings(HttpSettings):
    """Validated complete application configuration loaded from the environment."""

    openai_api_key: SecretStr = Field(repr=False)
    openai_model: str = Field(default="gpt-5.6", min_length=1, max_length=100)
    openai_store_responses: bool = False
    openai_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    openai_max_retries: int = Field(default=2, ge=0, le=5)

    chat_max_message_chars: int = Field(default=2000, ge=1, le=10_000)

    green_api_instance_id: str | None = Field(default=None, repr=False)
    green_api_token_instance: SecretStr | None = Field(default=None, repr=False)
    green_api_webhook_token: SecretStr | None = Field(default=None, repr=False)
    green_api_api_url: str = DEFAULT_GREEN_API_URL
    whatsapp_request_timeout_seconds: float = Field(default=15.0, gt=0, le=120)

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()
        if not secret.strip():
            raise ValueError("OPENAI_API_KEY is required")
        if secret != secret.strip():
            raise ValueError("OPENAI_API_KEY must not contain surrounding whitespace")
        return value

    @field_validator("openai_model")
    @classmethod
    def normalize_openai_model(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be blank")
        return normalized

    @field_validator("green_api_token_instance", "green_api_webhook_token")
    @classmethod
    def validate_optional_provider_secret(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return None
        secret = value.get_secret_value()
        if not secret.strip():
            raise ValueError("configured secret must not be blank")
        if secret != secret.strip():
            raise ValueError("configured secret must not contain surrounding whitespace")
        if "\r" in secret or "\n" in secret:
            raise ValueError("configured secret must not contain line breaks")
        return value

    @field_validator("green_api_token_instance")
    @classmethod
    def validate_green_api_token_instance(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return None
        if re.fullmatch(r"[A-Za-z0-9_-]{16,256}", value.get_secret_value()) is None:
            raise ValueError("GREEN_API_TOKEN_INSTANCE has an invalid format")
        return value

    @field_validator("green_api_instance_id")
    @classmethod
    def validate_green_api_instance_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value != value.strip() or not re.fullmatch(r"[1-9][0-9]{0,19}", value):
            raise ValueError("GREEN_API_INSTANCE_ID must contain 1 to 20 digits")
        return value

    @field_validator("green_api_api_url")
    @classmethod
    def validate_green_api_api_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        parsed_url = urlsplit(normalized)

        try:
            parsed_url.port
        except ValueError as exc:
            raise ValueError("GREEN_API_API_URL must use a valid port") from exc

        hostname = (parsed_url.hostname or "").lower()
        if (
            value != value.strip()
            or parsed_url.scheme != "https"
            or not hostname
            or not any(
                hostname == allowed_host or hostname.endswith(f".{allowed_host}")
                for allowed_host in ("green-api.com", "greenapi.com")
            )
            or parsed_url.username is not None
            or parsed_url.password is not None
            or parsed_url.path not in {"", "/"}
            or parsed_url.query
            or parsed_url.fragment
        ):
            raise ValueError("GREEN_API_API_URL must be an HTTPS GREEN-API host")

        return normalized


@lru_cache
def get_http_settings() -> HttpSettings:
    """Return HTTP settings without requiring provider credentials."""

    return HttpSettings()


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings instance per application process."""

    return Settings()
