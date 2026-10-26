from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SurveyOfferRequest(BaseModel):
    conversation_id: UUID
    identity_token: str | None = None


class SurveyResponseRequest(SurveyOfferRequest):
    satisfaction_score: int = Field(ge=1, le=5)
    resolution: Literal["yes", "partial", "no"] | None = None
    clarity_score: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        if value is not None and "\x00" in value:
            raise ValueError("El comentario contiene caracteres no permitidos")
        return value.strip() or None if value is not None else None


class SurveyStateResponse(BaseModel):
    state: Literal["offered", "submitted"]


class SatisfactionPointResponse(BaseModel):
    period_start: datetime
    offers: int
    responses: int
    satisfied: int
    clarity_count: int
    clarity_sum: int
    resolution_count: int
    resolved: int
    scores: dict[int, int]


class SatisfactionMetricsResponse(BaseModel):
    chatbot_id: UUID
    started_at: datetime | None
    ended_at: datetime | None
    interval: Literal["day", "week", "month"]
    offers: int
    responses: int
    satisfied: int
    participation_rate: float | None
    csat_rate: float | None
    clarity_count: int
    average_clarity: float | None
    resolution_count: int
    resolved: int
    resolution_rate: float | None
    scores: dict[int, int]
    series: list[SatisfactionPointResponse]


class SurveyCommentResponse(BaseModel):
    submitted_at: datetime
    comment: str


class SurveyCommentsPage(BaseModel):
    items: list[SurveyCommentResponse]
    total: int
    limit: int
    offset: int
