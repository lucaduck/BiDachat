from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chatbot, Query


class ChatbotMetricsNotFoundError(Exception):
    pass


class MetricsPeriodValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class MetricsSummary:
    chatbot_id: UUID
    started_at: datetime | None
    ended_at: datetime | None
    total_queries: int
    completed_queries: int
    failed_queries: int
    processing_queries: int
    measured_response_count: int
    average_response_time_ms: float | None


class MetricsService:
    async def get_metrics(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
    ) -> MetricsSummary:
        if (started_at is None) != (ended_at is None):
            raise MetricsPeriodValidationError
        if started_at is not None and ended_at is not None and started_at >= ended_at:
            raise MetricsPeriodValidationError
        if await session.get(Chatbot, chatbot_id) is None:
            raise ChatbotMetricsNotFoundError

        statement = select(
            func.count(Query.id).label("total_queries"),
            func.count(Query.id)
            .filter(Query.status == "completed")
            .label("completed_queries"),
            func.count(Query.id)
            .filter(Query.status == "failed")
            .label("failed_queries"),
            func.count(Query.id)
            .filter(Query.status == "processing")
            .label("processing_queries"),
            func.count(Query.response_time_ms)
            .filter(Query.status == "completed")
            .label("measured_response_count"),
            func.avg(Query.response_time_ms)
            .filter(Query.status == "completed")
            .label("average_response_time_ms"),
        ).where(Query.chatbot_id == chatbot_id)
        if started_at is not None and ended_at is not None:
            statement = statement.where(
                Query.received_at >= started_at,
                Query.received_at < ended_at,
            )

        row = (await session.execute(statement)).one()
        average = row.average_response_time_ms
        return MetricsSummary(
            chatbot_id=chatbot_id,
            started_at=started_at,
            ended_at=ended_at,
            total_queries=int(row.total_queries),
            completed_queries=int(row.completed_queries),
            failed_queries=int(row.failed_queries),
            processing_queries=int(row.processing_queries),
            measured_response_count=int(row.measured_response_count),
            average_response_time_ms=(float(average) if average is not None else None),
        )
