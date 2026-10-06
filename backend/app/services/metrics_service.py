from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chatbot, Query

MetricsInterval = Literal["day", "week", "month"]
MetricsStatus = Literal["completed", "failed", "processing"]


class ChatbotMetricsNotFoundError(Exception):
    pass


class MetricsPeriodValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class MetricsPoint:
    period_start: datetime
    total_queries: int = 0
    completed_queries: int = 0
    failed_queries: int = 0
    processing_queries: int = 0
    measured_response_count: int = 0
    average_response_time_ms: float | None = None


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
    interval: MetricsInterval
    status: MetricsStatus | None
    series: list[MetricsPoint]


def _period_start(value: datetime, interval: MetricsInterval) -> datetime:
    value = value.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    if interval == "week":
        return value - timedelta(days=value.weekday())
    if interval == "month":
        return value.replace(day=1)
    return value


def _next_period(value: datetime, interval: MetricsInterval) -> datetime:
    if interval == "month":
        return value.replace(
            year=value.year + (value.month == 12), month=value.month % 12 + 1
        )
    return value + timedelta(days=7 if interval == "week" else 1)


def _aggregates():
    return (
        func.count(Query.id).label("total_queries"),
        func.count(Query.id)
        .filter(Query.status == "completed")
        .label("completed_queries"),
        func.count(Query.id).filter(Query.status == "failed").label("failed_queries"),
        func.count(Query.id)
        .filter(Query.status == "processing")
        .label("processing_queries"),
        func.count(Query.response_time_ms)
        .filter(Query.status == "completed")
        .label("measured_response_count"),
        func.avg(Query.response_time_ms)
        .filter(Query.status == "completed")
        .label("average_response_time_ms"),
    )


def _values(row):
    return {
        "total_queries": int(row.total_queries),
        "completed_queries": int(row.completed_queries),
        "failed_queries": int(row.failed_queries),
        "processing_queries": int(row.processing_queries),
        "measured_response_count": int(row.measured_response_count),
        "average_response_time_ms": (
            float(row.average_response_time_ms)
            if row.average_response_time_ms is not None
            else None
        ),
    }


class MetricsService:
    async def get_metrics(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        interval: MetricsInterval = "day",
        status: MetricsStatus | None = None,
        include_series: bool = False,
    ) -> MetricsSummary:
        if (started_at is None) != (ended_at is None):
            raise MetricsPeriodValidationError
        if started_at is not None and ended_at is not None:
            if started_at.tzinfo is None or ended_at.tzinfo is None:
                raise MetricsPeriodValidationError
            if started_at >= ended_at:
                raise MetricsPeriodValidationError
        if interval not in {"day", "week", "month"} or status not in {
            None,
            "completed",
            "failed",
            "processing",
        }:
            raise MetricsPeriodValidationError
        if await session.get(Chatbot, chatbot_id) is None:
            raise ChatbotMetricsNotFoundError

        filters = [Query.chatbot_id == chatbot_id]
        if started_at is not None and ended_at is not None:
            filters.extend(
                [Query.received_at >= started_at, Query.received_at < ended_at]
            )
        if status is not None:
            filters.append(Query.status == status)
        series: list[MetricsPoint] = []
        if include_series:
            # UTC buckets are independent of the database server's local timezone.
            bucket = func.date_trunc(interval, func.timezone("UTC", Query.received_at))
            rows = (
                await session.execute(
                    select(bucket.label("period_start"), *_aggregates())
                    .where(*filters)
                    .group_by(bucket)
                    .order_by(bucket)
                    .limit(1001)
                )
            ).all()
            if len(rows) > 1000:
                raise MetricsPeriodValidationError
            # Totals and charts derive from the same database result, even while
            # new conversations are being recorded concurrently.
            values = [_values(item) for item in rows]
            summary_values = {
                key: sum(item[key] for item in values)
                for key in (
                    "total_queries",
                    "completed_queries",
                    "failed_queries",
                    "processing_queries",
                    "measured_response_count",
                )
            }
            measured = summary_values["measured_response_count"]
            summary_values["average_response_time_ms"] = (
                sum(
                    (item["average_response_time_ms"] or 0)
                    * item["measured_response_count"]
                    for item in values
                )
                / measured
                if measured
                else None
            )
            points = {
                item.period_start.replace(tzinfo=UTC): MetricsPoint(
                    period_start=item.period_start.replace(tzinfo=UTC), **_values(item)
                )
                for item in rows
            }
            first = (
                _period_start(started_at, interval)
                if started_at
                else min(points, default=None)
            )
            last = (
                _period_start(ended_at - timedelta(microseconds=1), interval)
                if ended_at
                else max(points, default=None)
            )
            if first is not None and last is not None:
                cursor = first
                while cursor <= last:
                    # Bound the payload; clients can select a coarser grouping.
                    if len(series) >= 1000:
                        raise MetricsPeriodValidationError
                    series.append(points.get(cursor, MetricsPoint(period_start=cursor)))
                    cursor = _next_period(cursor, interval)
        else:
            row = (await session.execute(select(*_aggregates()).where(*filters))).one()
            summary_values = _values(row)
        return MetricsSummary(
            chatbot_id=chatbot_id,
            started_at=started_at,
            ended_at=ended_at,
            **summary_values,
            interval=interval,
            status=status,
            series=series,
        )
