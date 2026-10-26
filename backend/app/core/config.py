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
EXTERNAL_GATEWAY_PROVIDERS = frozenset({"gemini", "openai", "openrouter", "vertex"})


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
    openai_models: str = ""
    openrouter_api_key: SecretStr | None = None
    openrouter_model: str = ""
    openrouter_models: str = ""
    openrouter_site_url: str = ""
    gemini_model: str = ""
    gemini_models: str = ""
    vertex_enabled: bool = False
    vertex_model: str = ""
    vertex_models: str = ""
    litellm_base_url: str = "http://litellm:4000"
    litellm_master_key: SecretStr | None = None
    external_ai_gateway_providers: str = ""
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
        configured = _configured_models(self.vertex_models)
        return configured or ((self.vertex_model,) if self.vertex_model else ())

    @property
    def configured_external_ai_gateway_providers(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                provider.strip().lower()
                for provider in self.external_ai_gateway_providers.split(",")
                if provider.strip()
            )
        )

    def configured_models_for_provider(self, provider: str) -> tuple[str, ...]:
        if provider == "vertex":
            return self.configured_vertex_models
        models_by_provider = {
            "gemini": (self.gemini_models, self.gemini_model),
            "openai": (self.openai_models, self.openai_model),
            "openrouter": (self.openrouter_models, self.openrouter_model),
        }
        configured = models_by_provider.get(provider)
        if configured is None:
            return ()
        listed, default = configured
        return _configured_models(listed) or (
            (default.strip(),) if default.strip() else ()
        )

    def provider_uses_gateway(self, provider: str) -> bool:
        return provider in self.configured_external_ai_gateway_providers or (
            provider == "vertex" and self.vertex_enabled
        )

    def gateway_model_available(self, provider: str, model: str) -> bool:
        if provider == "vertex":
            return self.vertex_model_available(model)
        return self.provider_uses_gateway(
            provider
        ) and model in self.configured_models_for_provider(provider)

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

    @field_validator("external_ai_gateway_providers")
    @classmethod
    def normalize_external_gateway_providers(cls, value: str) -> str:
        providers = []
        for provider in value.split(","):
            normalized = provider.strip().lower()
            if not normalized:
                continue
            if normalized not in EXTERNAL_GATEWAY_PROVIDERS:
                raise ValueError(
                    "EXTERNAL_AI_GATEWAY_PROVIDERS has an unsupported provider"
                )
            if normalized not in providers:
                providers.append(normalized)
        return ",".join(providers)

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
        gateway_providers = self.configured_external_ai_gateway_providers
        if gateway_providers and (
            self.litellm_master_key is None
            or len(self.litellm_master_key.get_secret_value().strip()) < 32
        ):
            raise ValueError(
                "EXTERNAL_AI_GATEWAY_PROVIDERS requires a gateway key of 32+ characters"
            )
        for provider in gateway_providers:
            if provider == "vertex" and not self.vertex_enabled:
                raise ValueError("Vertex gateway routing requires VERTEX_ENABLED=true")
            if not self.configured_models_for_provider(provider):
                raise ValueError(
                    "EXTERNAL_AI_GATEWAY_PROVIDERS requires an explicit "
                    f"{provider} model"
                )
        if (
            self.vision_provider in gateway_providers
            and not self.gateway_model_available(
                self.vision_provider, self.vision_model.strip()
            )
        ):
            raise ValueError("VISION_MODEL must be in the configured gateway catalogue")
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


def _configured_models(value: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(model.strip() for model in value.split(",") if model.strip())
    )
