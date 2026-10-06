from pydantic import BaseModel


class SystemSettingsResponse(BaseModel):
    gemini_configured: bool
    openai_configured: bool
    openrouter_configured: bool
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    document_max_size_bytes: int
    session_ttl_minutes: int
    widget_allowed_origins: list[str]
