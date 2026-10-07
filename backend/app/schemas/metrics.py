from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.services.metrics_service import MetricsInterval, MetricsStatus


class MetricsPointResponse(BaseModel):
    period_start: datetime
    total_queries: int
    completed_queries: int
    failed_queries: int
    processing_queries: int
    measured_response_count: int
    average_response_time_ms: float | None


class MetricsResponse(BaseModel):
    chatbot_id: UUID
    started_at: datetime | None
    ended_at: datetime | None
    total_queries: int
    completed_queries: int
    failed_queries: int
    processing_queries: int
    measured_response_count: int
    average_response_time_ms: float | None

    interval: MetricsInterval
    status: MetricsStatus | None
    series: list[MetricsPointResponse]
