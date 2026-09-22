from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
