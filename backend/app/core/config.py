from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EMBEDDING_DIMENSIONS = 768
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-2"
DEFAULT_DOCUMENT_MAX_SIZE_BYTES = 20 * 1024 * 1024


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: SecretStr | None = None
    embedding_provider: Literal["gemini", "ollama"] = "gemini"
    embedding_model: str = Field(
        default=DEFAULT_EMBEDDING_MODEL,
        min_length=1,
    )
    embedding_dimensions: int = Field(
        default=DEFAULT_EMBEDDING_DIMENSIONS,
        ge=1,
    )
    session_ttl_minutes: int = Field(default=480, ge=1, le=10_080)
    document_storage_path: Path = PROJECT_ROOT / "storage" / "documents"
    document_max_size_bytes: int = Field(
        default=DEFAULT_DOCUMENT_MAX_SIZE_BYTES,
        ge=1,
    )
    gemini_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    openai_model: str = ""
    openrouter_api_key: SecretStr | None = None
    openrouter_model: str = ""
    openrouter_site_url: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    ollama_context_length: int = Field(default=2048, ge=512, le=32768)
    ollama_timeout_seconds: int = Field(default=600, ge=10, le=600)
    widget_allowed_origins: str = ""

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError("OLLAMA_BASE_URL must be an HTTP(S) origin")
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
