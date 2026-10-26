import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete

from app.core.config import Settings
from app.database.session import Database
from app.models import Chatbot, Conversation, LlmModel, Query, User
from app.services.conversation_memory_service import (
    ConversationMemoryService,
    normalize_origin,
)


def test_origin_normalization_is_bounded_to_http_origins():
    assert normalize_origin("HTTPS://Example.COM:443") == "https://example.com:443"
    assert normalize_origin(None) == "same-origin"
    assert normalize_origin("javascript:alert(1)") == "same-origin"
    assert normalize_origin("https://user:secret@example.com") == "same-origin"


@pytest.mark.integration
def test_conversation_memory_is_persisted_isolated_and_cleaned():
    settings = Settings(
        conversation_ttl_hours=24,
        conversation_max_turns=2,
        conversation_max_chars=2000,
    )
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")
    asyncio.run(_exercise_memory(settings))


async def _exercise_memory(settings: Settings) -> None:
    database = Database.from_settings(settings)
    service = ConversationMemoryService(settings)
    user_id, model_id, first_bot_id, second_bot_id = (
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
    )
    query_id = uuid4()
    now = datetime.now(UTC)
    try:
        async with database.session() as session:
            session.add_all(
                [
                    User(
                        id=user_id,
                        email=f"memory-{user_id}@bidachat.test",
                        password_hash="test-hash",
                    ),
                    LlmModel(id=model_id, provider="vertex", model=f"test-{model_id}"),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    Chatbot(
                        id=first_bot_id,
                        created_by=user_id,
                        configured_llm_model_id=model_id,
                        name="Memory bot A",
                    ),
                    Chatbot(
                        id=second_bot_id,
                        created_by=user_id,
                        configured_llm_model_id=model_id,
                        name="Memory bot B",
                    ),
                ]
            )
            await session.flush()
            conversation = await service.resolve(
                session,
                chatbot_id=first_bot_id,
                requested_id=None,
                origin="https://dashboard.example",
                now=now,
            )
            query = Query(
                id=query_id,
                chatbot_id=first_bot_id,
                conversation_id=conversation.id,
                executed_llm_model_id=model_id,
                question="Me llamo Patricio",
                answer="Hola, Patricio",
                status="completed",
                completed_at=now + timedelta(seconds=1),
                response_time_ms=1000,
                received_at=now,
            )
            session.add(query)
            await session.flush()
            await service.save_successful_turn(
                session, conversation_id=conversation.id, query=query
            )
            await session.commit()

            restored = await service.resolve(
                session,
                chatbot_id=first_bot_id,
                requested_id=conversation.id,
                origin="https://dashboard.example",
                now=now + timedelta(minutes=1),
            )
            assert restored.id == conversation.id
            assert await service.recent_messages(
                session, conversation_id=restored.id
            ) == [("user", "Me llamo Patricio"), ("assistant", "Hola, Patricio")]

            expected_recent: list[tuple[str, str]] = []
            for offset, marker in enumerate(("segundo", "tercero"), start=2):
                question = f"{marker}:" + "q" * 292
                answer = f"{marker}:" + "a" * 292
                recent_query = Query(
                    id=uuid4(),
                    chatbot_id=first_bot_id,
                    conversation_id=conversation.id,
                    executed_llm_model_id=model_id,
                    question=question,
                    answer=answer,
                    status="completed",
                    completed_at=now + timedelta(seconds=offset * 2 + 1),
                    response_time_ms=1000,
                    received_at=now + timedelta(seconds=offset * 2),
                )
                session.add(recent_query)
                await session.flush()
                await service.save_successful_turn(
                    session,
                    conversation_id=conversation.id,
                    query=recent_query,
                )
                expected_recent.extend((("user", question), ("assistant", answer)))
            await session.commit()
            assert (
                await service.recent_messages(session, conversation_id=restored.id)
                == expected_recent
            )
            character_limited = ConversationMemoryService(
                settings.model_copy(update={"conversation_max_chars": 1000})
            )
            limited_messages = await character_limited.recent_messages(
                session, conversation_id=restored.id
            )
            assert limited_messages == expected_recent[-2:]
            assert sum(len(content) for _, content in limited_messages) <= 1000

            isolated = await service.resolve(
                session,
                chatbot_id=second_bot_id,
                requested_id=conversation.id,
                origin="https://dashboard.example",
                now=now + timedelta(minutes=1),
            )
            assert isolated.id != conversation.id
            assert (
                await service.recent_messages(session, conversation_id=isolated.id)
                == []
            )
            other_origin = await service.resolve(
                session,
                chatbot_id=first_bot_id,
                requested_id=conversation.id,
                origin="https://other.example",
                now=now + timedelta(minutes=1),
            )
            assert other_origin.id != conversation.id
            assert (
                await service.recent_messages(session, conversation_id=other_origin.id)
                == []
            )

            signed = await service.resolve(
                session,
                chatbot_id=first_bot_id,
                requested_id=None,
                origin="https://dashboard.example",
                identity_hash="a" * 64,
                now=now,
            )
            signed_query = Query(
                id=uuid4(),
                chatbot_id=first_bot_id,
                conversation_id=signed.id,
                executed_llm_model_id=model_id,
                question="Me llamo Ana",
                answer="Hola, Ana",
                status="completed",
                completed_at=now + timedelta(seconds=1),
                response_time_ms=1000,
                received_at=now,
            )
            session.add(signed_query)
            await session.flush()
            await service.save_successful_turn(
                session, conversation_id=signed.id, query=signed_query
            )
            assert (
                await service.resolve(
                    session,
                    chatbot_id=first_bot_id,
                    requested_id=signed.id,
                    origin="https://dashboard.example",
                    identity_hash="a" * 64,
                    now=now,
                )
            ).id == signed.id
            assert await service.recent_messages(
                session, conversation_id=signed.id
            ) == [
                ("user", "Me llamo Ana"),
                ("assistant", "Hola, Ana"),
            ]
            for other_identity in (None, "b" * 64):
                different = await service.resolve(
                    session,
                    chatbot_id=first_bot_id,
                    requested_id=signed.id,
                    origin="https://dashboard.example",
                    identity_hash=other_identity,
                    now=now,
                )
                assert different.id != signed.id
                assert (
                    await service.recent_messages(session, conversation_id=different.id)
                    == []
                )

            cleanup_time = now + timedelta(hours=25)
            deleted_count = await service.cleanup_expired(session, now=cleanup_time)
            assert deleted_count >= 3
            await session.commit()
            for conversation_id in (
                conversation.id,
                isolated.id,
                other_origin.id,
            ):
                assert await session.get(Conversation, conversation_id) is None
            persisted_query = await session.get(Query, query_id)
            assert persisted_query is not None
            await session.refresh(persisted_query)
            assert persisted_query.conversation_id is None
    finally:
        async with database.session() as session:
            await session.execute(delete(Chatbot).where(Chatbot.created_by == user_id))
            await session.execute(delete(User).where(User.id == user_id))
            model = await session.get(LlmModel, model_id)
            if model is not None:
                await session.delete(model)
            await session.commit()
        await database.dispose()
