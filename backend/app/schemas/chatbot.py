from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LlmModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    model: str


class ChatbotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    behavior_instructions: str = Field(default="", max_length=10_000)
    configured_llm_model_id: UUID

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
    configured_llm_model: LlmModelResponse
    created_at: datetime
    updated_at: datetime
