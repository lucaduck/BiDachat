from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LlmModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    model: str


class WidgetSettings(BaseModel):
    primary_color: str = Field(default="#14a8ce", pattern=r"^#[0-9a-fA-F]{6}$")
    icon: Literal["bot", "chat", "chart", "book", "sparkles", "headset"] = "bot"
    welcome_message: str = Field(
        default="Hola, ¿en qué puedo ayudarte con este dashboard?",
        max_length=300,
    )


class ChatbotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    behavior_instructions: str = Field(default="", max_length=10_000)
    configured_llm_model_id: UUID
    widget_settings: WidgetSettings = Field(default_factory=WidgetSettings)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Chatbot name must not be blank")
        return normalized


class ChatbotUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    behavior_instructions: str = Field(default="", max_length=10_000)
    configured_llm_model_id: UUID
    widget_settings: WidgetSettings | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Chatbot name must not be blank")
        return normalized


class ChatbotResponse(BaseModel):
    id: UUID
    created_by: UUID
    name: str
    description: str | None
    behavior_instructions: str
    widget_settings: WidgetSettings
    configured_llm_model: LlmModelResponse
    created_at: datetime
    updated_at: datetime
