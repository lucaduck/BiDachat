from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chatbot, ConversationFeedback
from app.schemas.satisfaction import (
    SatisfactionMetricsResponse,
    SatisfactionPointResponse,
    SurveyCommentResponse,
    SurveyCommentsPage,
)
from app.services.metrics_service import (
    ChatbotMetricsNotFoundError,
    MetricsInterval,
    MetricsPeriodValidationError,
    _next_period,
    _period_start,
)


def _aggregates():
    feedback = ConversationFeedback
    return (
        func.count(feedback.id).label("offers"),
        func.count(feedback.submitted_at).label("responses"),
        func.count(feedback.id)
        .filter(feedback.satisfaction_score >= 4)
        .label("satisfied"),
        func.count(feedback.clarity_score).label("clarity_count"),
        func.coalesce(func.sum(feedback.clarity_score), 0).label("clarity_sum"),
        func.count(feedback.resolution).label("resolution_count"),
        func.count(feedback.id).filter(feedback.resolution == "yes").label("resolved"),
        *(
            func.count(feedback.id)
            .filter(feedback.satisfaction_score == score)
            .label(f"score_{score}")
            for score in range(1, 6)
        ),
    )


def _counts(row) -> dict:
    return {
        "offers": int(row.offers),
        "responses": int(row.responses),
        "satisfied": int(row.satisfied),
        "clarity_count": int(row.clarity_count),
        "clarity_sum": int(row.clarity_sum),
        "resolution_count": int(row.resolution_count),
        "resolved": int(row.resolved),
        "scores": {score: int(getattr(row, f"score_{score}")) for score in range(1, 6)},
    }


class SatisfactionMetricsService:
    @staticmethod
    async def _validate(
        session: AsyncSession,
        chatbot_id: UUID,
        started_at: datetime | None,
        ended_at: datetime | None,
        interval: MetricsInterval,
    ) -> None:
        if (started_at is None) != (ended_at is None):
            raise MetricsPeriodValidationError
        if started_at is not None and ended_at is not None:
            if (
                started_at.tzinfo is None
                or ended_at.tzinfo is None
                or started_at >= ended_at
            ):
                raise MetricsPeriodValidationError
        if interval not in {"day", "week", "month"}:
            raise MetricsPeriodValidationError
        if await session.get(Chatbot, chatbot_id) is None:
            raise ChatbotMetricsNotFoundError

    @staticmethod
    def _filters(
        chatbot_id: UUID, started_at: datetime | None, ended_at: datetime | None
    ) -> list:
        filters = [ConversationFeedback.chatbot_id == chatbot_id]
        if started_at is not None and ended_at is not None:
            filters.extend(
                [
                    ConversationFeedback.offered_at >= started_at,
                    ConversationFeedback.offered_at < ended_at,
                ]
            )
        return filters

    async def get_metrics(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        started_at: datetime | None,
        ended_at: datetime | None,
        interval: MetricsInterval,
    ) -> SatisfactionMetricsResponse:
        await self._validate(session, chatbot_id, started_at, ended_at, interval)
        bucket = func.date_trunc(
            interval, func.timezone("UTC", ConversationFeedback.offered_at)
        )
        rows = (
            await session.execute(
                select(bucket.label("period_start"), *_aggregates())
                .where(*self._filters(chatbot_id, started_at, ended_at))
                .group_by(bucket)
                .order_by(bucket)
                .limit(1001)
            )
        ).all()
        if len(rows) > 1000:
            raise MetricsPeriodValidationError
        points = {
            row.period_start.replace(tzinfo=UTC): SatisfactionPointResponse(
                period_start=row.period_start.replace(tzinfo=UTC), **_counts(row)
            )
            for row in rows
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
        series = []
        cursor = first
        while cursor is not None and last is not None and cursor <= last:
            if len(series) >= 1000:
                raise MetricsPeriodValidationError
            series.append(
                points.get(
                    cursor,
                    SatisfactionPointResponse(
                        period_start=cursor,
                        offers=0,
                        responses=0,
                        satisfied=0,
                        clarity_count=0,
                        clarity_sum=0,
                        resolution_count=0,
                        resolved=0,
                        scores={score: 0 for score in range(1, 6)},
                    ),
                )
            )
            cursor = _next_period(cursor, interval)
        totals = {
            key: sum(getattr(point, key) for point in series)
            for key in (
                "offers",
                "responses",
                "satisfied",
                "clarity_count",
                "clarity_sum",
                "resolution_count",
                "resolved",
            )
        }
        scores = {
            score: sum(point.scores[score] for point in series) for score in range(1, 6)
        }
        return SatisfactionMetricsResponse(
            chatbot_id=chatbot_id,
            started_at=started_at,
            ended_at=ended_at,
            interval=interval,
            offers=totals["offers"],
            responses=totals["responses"],
            satisfied=totals["satisfied"],
            participation_rate=(
                totals["responses"] / totals["offers"] if totals["offers"] else None
            ),
            csat_rate=(
                totals["satisfied"] / totals["responses"]
                if totals["responses"]
                else None
            ),
            clarity_count=totals["clarity_count"],
            average_clarity=(
                totals["clarity_sum"] / totals["clarity_count"]
                if totals["clarity_count"]
                else None
            ),
            resolution_count=totals["resolution_count"],
            resolved=totals["resolved"],
            resolution_rate=(
                totals["resolved"] / totals["resolution_count"]
                if totals["resolution_count"]
                else None
            ),
            scores=scores,
            series=series,
        )

    async def get_comments(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        started_at: datetime | None,
        ended_at: datetime | None,
        limit: int,
        offset: int,
    ) -> SurveyCommentsPage:
        await self._validate(session, chatbot_id, started_at, ended_at, "day")
        filters = self._filters(chatbot_id, started_at, ended_at)
        filters.append(ConversationFeedback.comment.is_not(None))
        total = await session.scalar(
            select(func.count(ConversationFeedback.id)).where(*filters)
        )
        rows = (
            await session.execute(
                select(ConversationFeedback.submitted_at, ConversationFeedback.comment)
                .where(*filters)
                .order_by(
                    ConversationFeedback.submitted_at.desc(),
                    ConversationFeedback.id.desc(),
                )
                .limit(limit)
                .offset(offset)
            )
        ).all()
        return SurveyCommentsPage(
            items=[
                SurveyCommentResponse(submitted_at=row[0], comment=row[1])
                for row in rows
            ],
            total=total or 0,
            limit=limit,
            offset=offset,
        )
