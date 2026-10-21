"""PostgreSQL acceptance of Vertex catalogue and historical execution identity."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.core.config import Settings
from app.database.session import Database
from app.llm.provider import LlmProvider, ProviderConfigurationError
from app.models import Chatbot, LlmModel, Query, User
from app.services.chatbot_service import ChatbotService, LlmModelNotFoundError
from app.services.conversation_service import ConversationService


@pytest.mark.integration
def test_vertex_switch_and_retirement_preserve_queries(monkeypatch):
    model_suffix = uuid4().hex[:8]
    active_model = f"gemini-active-test-{model_suffix}"
    retired_model = f"gemini-retired-test-{model_suffix}"
    settings = Settings(
        vertex_enabled=True,
        vertex_model=active_model,
        vertex_models=active_model,
        litellm_master_key="test-gateway-key-" * 3,
        embedding_provider="gemini",
        gemini_api_key=None,
    )
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")

    async def run():
        database = Database.from_settings(settings)
        user_id, first_id, second_id, bot_id = [uuid4() for _ in range(4)]
        try:
            async with database.session() as session:
                session.add(
                    User(
                        id=user_id,
                        email=f"vertex-{user_id}@example.test",
                        password_hash="test",
                    )
                )
                session.add_all(
                    [
                        LlmModel(
                            id=first_id, provider="vertex", model=settings.vertex_model
                        ),
                        LlmModel(id=second_id, provider="vertex", model=retired_model),
                    ]
                )
                await session.flush()
                session.add(
                    Chatbot(
                        id=bot_id,
                        created_by=user_id,
                        name="Vertex test",
                        configured_llm_model_id=first_id,
                        behavior_instructions="",
                    )
                )
                await session.commit()
                service = ChatbotService(settings)
                models = await service.list_llm_models(session)
                assert first_id in {model.id for model in models}
                assert second_id not in {model.id for model in models}

                async def answer(self, **kwargs):
                    if not self.settings.vertex_model_available(kwargs["model"]):
                        raise ProviderConfigurationError("Unavailable")
                    return "42"

                monkeypatch.setattr(LlmProvider, "answer", answer)
                conversation = ConversationService(settings)
                completed = await conversation.ask(
                    session,
                    chatbot_id=bot_id,
                    question="Total?",
                    image=None,
                    image_mime_type=None,
                )
                assert completed.executed_llm_model_id == first_id
                assert completed.response_time_ms is not None
                changed = settings.model_copy(
                    update={
                        "vertex_model": retired_model,
                        "vertex_models": retired_model,
                    }
                )
                await ChatbotService(changed).update_chatbot(
                    session,
                    bot_id,
                    configured_llm_model_id=second_id,
                    name="Vertex test",
                    description=None,
                    behavior_instructions="",
                    widget_settings=None,
                )
                await session.commit()
                with pytest.raises(LlmModelNotFoundError):
                    await ChatbotService(changed)._get_llm_model(session, first_id)
                with pytest.raises(ProviderConfigurationError):
                    await conversation.ask(
                        session,
                        chatbot_id=bot_id,
                        question="Fails explicitly",
                        image=None,
                        image_mime_type=None,
                    )
                queries = list(
                    await session.scalars(
                        select(Query)
                        .where(Query.chatbot_id == bot_id)
                        .order_by(Query.received_at)
                    )
                )
                assert len(queries) == 2
                assert queries[0].executed_llm_model_id == first_id
                assert queries[1].executed_llm_model_id == second_id
                assert queries[1].error_code == "provider_error"
                assert await session.get(LlmModel, first_id) is not None
        finally:
            async with database.session() as session:
                await session.execute(delete(Chatbot).where(Chatbot.id == bot_id))
                await session.execute(
                    delete(LlmModel).where(LlmModel.id.in_([first_id, second_id]))
                )
                await session.execute(delete(User).where(User.id == user_id))
                await session.commit()
            await database.dispose()

    asyncio.run(run())
