from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chatbot, LlmModel


class ChatbotNotFoundError(Exception):
    pass


class LlmModelNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ChatbotDetails:
    chatbot: Chatbot
    llm_model: LlmModel


class ChatbotService:
    async def list_chatbots(self, session: AsyncSession) -> list[ChatbotDetails]:
        result = await session.execute(
            select(Chatbot, LlmModel)
            .join(LlmModel, Chatbot.configured_llm_model_id == LlmModel.id)
            .order_by(Chatbot.created_at, Chatbot.id)
        )
        return [
            ChatbotDetails(chatbot=chatbot, llm_model=llm_model)
            for chatbot, llm_model in result.all()
        ]

    async def list_llm_models(self, session: AsyncSession) -> list[LlmModel]:
        result = await session.scalars(
            select(LlmModel).order_by(LlmModel.provider, LlmModel.model)
        )
        return list(result.all())

    async def get_chatbot(
        self,
        session: AsyncSession,
        chatbot_id: UUID,
    ) -> ChatbotDetails:
        result = await session.execute(
            select(Chatbot, LlmModel)
            .join(LlmModel, Chatbot.configured_llm_model_id == LlmModel.id)
            .where(Chatbot.id == chatbot_id)
        )
        row = result.one_or_none()
        if row is None:
            raise ChatbotNotFoundError
        chatbot, llm_model = row
        return ChatbotDetails(chatbot=chatbot, llm_model=llm_model)

    async def create_chatbot(
        self,
        session: AsyncSession,
        *,
        created_by: UUID,
        configured_llm_model_id: UUID,
        name: str,
        description: str | None,
        behavior_instructions: str,
        widget_settings: dict,
    ) -> ChatbotDetails:
        llm_model = await self._get_llm_model(session, configured_llm_model_id)
        chatbot = Chatbot(
            created_by=created_by,
            configured_llm_model_id=llm_model.id,
            name=name.strip(),
            description=_normalize_optional_text(description),
            behavior_instructions=behavior_instructions.strip(),
            widget_settings=widget_settings,
        )
        session.add(chatbot)
        await session.flush()
        return ChatbotDetails(chatbot=chatbot, llm_model=llm_model)

    async def update_chatbot(
        self,
        session: AsyncSession,
        chatbot_id: UUID,
        *,
        configured_llm_model_id: UUID,
        name: str,
        description: str | None,
        behavior_instructions: str,
        widget_settings: dict | None,
    ) -> ChatbotDetails:
        chatbot = await session.get(Chatbot, chatbot_id)
        if chatbot is None:
            raise ChatbotNotFoundError
        llm_model = await self._get_llm_model(session, configured_llm_model_id)

        chatbot.configured_llm_model_id = llm_model.id
        chatbot.name = name.strip()
        chatbot.description = _normalize_optional_text(description)
        chatbot.behavior_instructions = behavior_instructions.strip()
        if widget_settings is not None:
            chatbot.widget_settings = widget_settings
        chatbot.updated_at = datetime.now(UTC)
        await session.flush()
        return ChatbotDetails(chatbot=chatbot, llm_model=llm_model)

    async def delete_chatbot(
        self,
        session: AsyncSession,
        chatbot_id: UUID,
    ) -> None:
        chatbot = await session.get(Chatbot, chatbot_id)
        if chatbot is None:
            raise ChatbotNotFoundError
        await session.delete(chatbot)
        await session.flush()

    async def _get_llm_model(
        self,
        session: AsyncSession,
        llm_model_id: UUID,
    ) -> LlmModel:
        llm_model = await session.get(LlmModel, llm_model_id)
        if llm_model is None:
            raise LlmModelNotFoundError
        return llm_model


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
