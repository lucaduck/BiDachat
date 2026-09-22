from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chatbot, Query


class ChatbotQueryNotFoundError(Exception):
    pass


class QueryNotFoundError(Exception):
    pass


class QueryStateError(Exception):
    pass


class QueryValidationError(Exception):
    pass


class QueryService:
    async def start_query(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        question: str,
        has_image: bool,
        received_at: datetime | None = None,
    ) -> Query:
        chatbot = await session.scalar(
            select(Chatbot)
            .where(Chatbot.id == chatbot_id)
            .with_for_update(key_share=True)
        )
        if chatbot is None:
            raise ChatbotQueryNotFoundError

        normalized_question = question.strip()
        if not normalized_question:
            raise QueryValidationError("Question must not be blank")

        query = Query(
            chatbot_id=chatbot_id,
            executed_llm_model_id=chatbot.configured_llm_model_id,
            question=normalized_question,
            has_image=has_image,
            received_at=received_at or datetime.now(UTC),
        )
        session.add(query)
        await session.flush()
        return query

    async def complete_query(
        self,
        session: AsyncSession,
        *,
        query_id: UUID,
        answer: str,
        completed_at: datetime | None = None,
    ) -> Query:
        query = await self._get_processing_query(session, query_id)
        normalized_answer = answer.strip()
        if not normalized_answer:
            raise QueryValidationError("Answer must not be blank")

        finished_at = completed_at or datetime.now(UTC)
        response_time_ms = _elapsed_milliseconds(query.received_at, finished_at)
        query.answer = normalized_answer
        query.status = "completed"
        query.completed_at = finished_at
        query.response_time_ms = response_time_ms
        await session.flush()
        return query

    async def fail_query(
        self,
        session: AsyncSession,
        *,
        query_id: UUID,
        error_code: str,
        completed_at: datetime | None = None,
    ) -> Query:
        query = await self._get_processing_query(session, query_id)
        normalized_error_code = error_code.strip()
        if not normalized_error_code:
            raise QueryValidationError("Error code must not be blank")

        query.status = "failed"
        query.error_code = normalized_error_code
        if completed_at is not None:
            query.completed_at = completed_at
            query.response_time_ms = _elapsed_milliseconds(
                query.received_at,
                completed_at,
            )
        await session.flush()
        return query

    async def _get_processing_query(
        self,
        session: AsyncSession,
        query_id: UUID,
    ) -> Query:
        query = await session.get(Query, query_id)
        if query is None:
            raise QueryNotFoundError
        if query.status != "processing":
            raise QueryStateError
        return query


def _elapsed_milliseconds(received_at: datetime, completed_at: datetime) -> int:
    elapsed_ms = int((completed_at - received_at).total_seconds() * 1000)
    if elapsed_ms < 0:
        raise QueryValidationError("Completion must not precede reception")
    return elapsed_ms
