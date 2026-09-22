import asyncio
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete

from app.core.config import Settings
from app.database.session import Database
from app.models import Chatbot, LlmModel, User
from app.services.metrics_service import MetricsService
from app.services.query_service import QueryService


@pytest.mark.integration
def test_query_records_and_metrics_are_isolated_and_handle_interruptions():
    settings = Settings()
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")

    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        runner.run(_exercise_query_metrics(settings))


async def _exercise_query_metrics(settings: Settings) -> None:
    database = Database.from_settings(settings)
    query_service = QueryService()
    metrics_service = MetricsService()
    user_id = uuid4()
    model_a_id = uuid4()
    model_b_id = uuid4()
    chatbot_a_id = uuid4()
    chatbot_b_id = uuid4()
    received_at = datetime(2026, 9, 22, 12, tzinfo=UTC)

    try:
        async with database.session() as session:
            session.add_all(
                [
                    User(
                        id=user_id,
                        email=f"metrics-{user_id}@bidachat.test",
                        password_hash="integration-hash",
                    ),
                    LlmModel(
                        id=model_a_id,
                        provider="test-provider",
                        model=f"metrics-model-a-{model_a_id}",
                    ),
                    LlmModel(
                        id=model_b_id,
                        provider="test-provider",
                        model=f"metrics-model-b-{model_b_id}",
                    ),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    Chatbot(
                        id=chatbot_a_id,
                        created_by=user_id,
                        configured_llm_model_id=model_a_id,
                        name="Chatbot de mÃ©tricas A",
                    ),
                    Chatbot(
                        id=chatbot_b_id,
                        created_by=user_id,
                        configured_llm_model_id=model_a_id,
                        name="Chatbot de mÃ©tricas B",
                    ),
                ]
            )
            await session.commit()

        async with database.session() as session:
            completed = await query_service.start_query(
                session,
                chatbot_id=chatbot_a_id,
                question="Pregunta textual",
                has_image=False,
                received_at=received_at,
            )
            chatbot_a = await session.get(Chatbot, chatbot_a_id)
            assert chatbot_a is not None
            chatbot_a.configured_llm_model_id = model_b_id
            await query_service.complete_query(
                session,
                query_id=completed.id,
                answer="Respuesta lista",
                completed_at=received_at + timedelta(milliseconds=120),
            )

            observed_failure = await query_service.start_query(
                session,
                chatbot_id=chatbot_a_id,
                question="Pregunta con imagen",
                has_image=True,
                received_at=received_at + timedelta(seconds=1),
            )
            await query_service.fail_query(
                session,
                query_id=observed_failure.id,
                error_code="LLM_TIMEOUT",
                completed_at=received_at + timedelta(seconds=1, milliseconds=80),
            )

            interrupted = await query_service.start_query(
                session,
                chatbot_id=chatbot_a_id,
                question="Pregunta interrumpida",
                has_image=False,
                received_at=received_at + timedelta(seconds=2),
            )
            await query_service.fail_query(
                session,
                query_id=interrupted.id,
                error_code="PROCESS_INTERRUPTED",
            )

            other_chatbot_query = await query_service.start_query(
                session,
                chatbot_id=chatbot_b_id,
                question="Pregunta exclusiva B",
                has_image=False,
                received_at=received_at,
            )
            await query_service.complete_query(
                session,
                query_id=other_chatbot_query.id,
                answer="Respuesta B",
                completed_at=received_at + timedelta(milliseconds=200),
            )
            await session.commit()

        async with database.session() as session:
            metrics_a = await metrics_service.get_metrics(
                session,
                chatbot_id=chatbot_a_id,
                started_at=received_at - timedelta(seconds=1),
                ended_at=received_at + timedelta(minutes=1),
            )
            assert metrics_a.total_queries == 3
            assert metrics_a.completed_queries == 1
            assert metrics_a.failed_queries == 2
            assert metrics_a.processing_queries == 0
            assert metrics_a.measured_response_count == 1
            assert metrics_a.average_response_time_ms == 120.0

            metrics_b = await metrics_service.get_metrics(
                session,
                chatbot_id=chatbot_b_id,
            )
            assert metrics_b.total_queries == 1
            assert metrics_b.average_response_time_ms == 200.0

            empty_metrics = await metrics_service.get_metrics(
                session,
                chatbot_id=chatbot_a_id,
                started_at=received_at + timedelta(days=1),
                ended_at=received_at + timedelta(days=2),
            )
            assert empty_metrics.total_queries == 0
            assert empty_metrics.average_response_time_ms is None
        async with database.session() as session:
            assert completed.executed_llm_model_id == model_a_id
            assert observed_failure.has_image is True
            assert interrupted.completed_at is None
            assert interrupted.response_time_ms is None
    finally:
        async with database.session() as session:
            await session.execute(delete(Chatbot).where(Chatbot.created_by == user_id))
            user = await session.get(User, user_id)
            if user is not None:
                await session.delete(user)
            for model_id in (model_a_id, model_b_id):
                model = await session.get(LlmModel, model_id)
                if model is not None:
                    await session.delete(model)
            await session.commit()
        await database.dispose()
