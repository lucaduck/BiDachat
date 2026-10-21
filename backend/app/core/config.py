from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
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
    conversation_ttl_hours: int = Field(default=24, ge=1, le=720)
    conversation_max_turns: int = Field(default=12, ge=1, le=100)
    conversation_max_chars: int = Field(default=12_000, ge=1_000, le=100_000)
    conversation_cleanup_interval_minutes: int = Field(default=60, ge=1, le=1440)
    widget_identity_master_key: SecretStr | None = None
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
    vertex_enabled: bool = False
    vertex_model: str = ""
    vertex_models: str = ""
    litellm_base_url: str = "http://litellm:4000"
    litellm_master_key: SecretStr | None = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    vision_provider: Literal["ollama", "gemini", "openai", "openrouter", "vertex"] = (
        "ollama"
    )
    vision_model: str = ""
    ollama_context_length: int = Field(default=2048, ge=512, le=32768)
    ollama_timeout_seconds: int = Field(default=600, ge=10, le=600)
    widget_allowed_origins: str = ""

    @field_validator("widget_allowed_origins")
    @classmethod
    def validate_widget_origins(cls, value: str) -> str:
        origins = []
        for entry in value.split(","):
            origin = entry.strip()
            if not origin:
                continue
            try:
                parsed = urlsplit(origin)
                port = parsed.port
                hostname = parsed.hostname
                valid = (
                    parsed.scheme in {"http", "https"}
                    and hostname
                    and parsed.username is None
                    and parsed.password is None
                    and parsed.path in {"", "/"}
                    and "?" not in origin
                    and "#" not in origin
                    and not any(c.isspace() or c in "\\\\*%" for c in origin)
                    and origin.isascii()
                    and port != 0
                )
                if not valid:
                    raise ValueError
                host = f"[{hostname}]" if ":" in hostname else hostname
                default_port = 443 if parsed.scheme == "https" else 80
                suffix = f":{port}" if port and port != default_port else ""
                normalized = f"{parsed.scheme}://{host}{suffix}"
            except ValueError as exc:
                raise ValueError(
                    "WIDGET_ALLOWED_ORIGINS requires explicit HTTP(S) origins"
                ) from exc
            if normalized not in origins:
                origins.append(normalized)
        return ",".join(origins)

    @field_validator("widget_identity_master_key")
    @classmethod
    def validate_widget_identity_master_key(
        cls, value: SecretStr | None
    ) -> SecretStr | None:
        if value is None or not value.get_secret_value():
            return None
        if len(value.get_secret_value()) < 32:
            raise ValueError(
                "WIDGET_IDENTITY_MASTER_KEY must have at least 32 characters"
            )
        return value

    @property
    def effective_vision_model(self) -> str:
        model = self.vision_model.strip()
        if not model and self.vision_provider == "ollama":
            model = self.ollama_model.strip()
        return model

    @property
    def configured_vertex_models(self) -> tuple[str, ...]:
        configured = tuple(
            dict.fromkeys(
                model.strip()
                for model in self.vertex_models.split(",")
                if model.strip()
            )
        )
        return configured or ((self.vertex_model,) if self.vertex_model else ())

    def vertex_model_available(self, model: str) -> bool:
        return self.vertex_enabled and model in self.configured_vertex_models

    @field_validator("vertex_model")
    @classmethod
    def normalize_vertex_model(cls, value: str) -> str:
        value = value.strip()
        if value and (
            not value.startswith("gemini-")
            or not all(char.isalnum() or char in "-." for char in value)
        ):
            raise ValueError("VERTEX_MODEL must be an explicit Gemini model ID")
        return value

    @field_validator("vertex_models")
    @classmethod
    def normalize_vertex_models(cls, value: str) -> str:
        models = []
        for model in value.split(","):
            normalized = cls.normalize_vertex_model(model)
            if normalized and normalized not in models:
                models.append(normalized)
        return ",".join(models)

    @model_validator(mode="after")
    def validate_vertex_settings(self) -> "Settings":
        if self.vertex_enabled and (
            not self.vertex_model
            or self.litellm_master_key is None
            or len(self.litellm_master_key.get_secret_value().strip()) < 32
        ):
            raise ValueError(
                "Vertex requires VERTEX_MODEL and a gateway key of 32+ characters"
            )
        if (
            self.vertex_enabled
            and self.vertex_model not in self.configured_vertex_models
        ):
            raise ValueError("VERTEX_MODEL must be included in VERTEX_MODELS")
        if self.vision_provider == "vertex" and not self.vertex_model_available(
            self.vision_model.strip()
        ):
            raise ValueError("VISION_MODEL must be an enabled VERTEX_MODELS entry")
        return self

    @field_validator("ollama_base_url", "litellm_base_url")
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
            raise ValueError("Provider URL must be an HTTP(S) origin")
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
