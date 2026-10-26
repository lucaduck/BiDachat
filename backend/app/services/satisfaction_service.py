from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, ConversationFeedback, Query
from app.services.conversation_memory_service import normalize_origin


class SurveyConversationUnavailableError(Exception):
    pass


class SurveyAlreadyAnsweredError(Exception):
    pass


class SatisfactionService:
    async def _eligible_conversation(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        conversation_id: UUID,
        origin: str,
        identity_hash: str | None,
    ) -> Conversation:
        conversation = await session.scalar(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .with_for_update()
        )
        if (
            conversation is None
            or conversation.chatbot_id != chatbot_id
            or conversation.origin != normalize_origin(origin)
            or conversation.identity_hash != identity_hash
            or conversation.expires_at <= datetime.now(UTC)
        ):
            raise SurveyConversationUnavailableError
        completed = await session.scalar(
            select(
                exists().where(
                    Query.conversation_id == conversation_id,
                    Query.chatbot_id == chatbot_id,
                    Query.status == "completed",
                )
            )
        )
        if not completed:
            raise SurveyConversationUnavailableError
        return conversation

    async def offer(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        conversation_id: UUID,
        origin: str,
        identity_hash: str | None,
    ) -> ConversationFeedback:
        await self._eligible_conversation(
            session,
            chatbot_id=chatbot_id,
            conversation_id=conversation_id,
            origin=origin,
            identity_hash=identity_hash,
        )
        feedback = await session.scalar(
            select(ConversationFeedback)
            .where(ConversationFeedback.conversation_id == conversation_id)
            .with_for_update()
        )
        if feedback is None:
            feedback = ConversationFeedback(
                id=uuid4(),
                chatbot_id=chatbot_id,
                conversation_id=conversation_id,
                offered_at=datetime.now(UTC),
            )
            session.add(feedback)
            await session.flush()
        return feedback

    async def submit(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        conversation_id: UUID,
        origin: str,
        identity_hash: str | None,
        satisfaction_score: int,
        resolution: str | None,
        clarity_score: int | None,
        comment: str | None,
    ) -> ConversationFeedback:
        await self._eligible_conversation(
            session,
            chatbot_id=chatbot_id,
            conversation_id=conversation_id,
            origin=origin,
            identity_hash=identity_hash,
        )
        feedback = await session.scalar(
            select(ConversationFeedback)
            .where(ConversationFeedback.conversation_id == conversation_id)
            .with_for_update()
        )
        if feedback is None or feedback.chatbot_id != chatbot_id:
            raise SurveyConversationUnavailableError
        values = (satisfaction_score, resolution, clarity_score, comment)
        if feedback.submitted_at is not None:
            saved = (
                feedback.satisfaction_score,
                feedback.resolution,
                feedback.clarity_score,
                feedback.comment,
            )
            if values != saved:
                raise SurveyAlreadyAnsweredError
            return feedback
        feedback.satisfaction_score = satisfaction_score
        feedback.resolution = resolution
        feedback.clarity_score = clarity_score
        feedback.comment = comment
        feedback.submitted_at = datetime.now(UTC)
        await session.flush()
        return feedback

    async def redact_expired_comments(
        self, session: AsyncSession, *, now: datetime | None = None
    ) -> int:
        cutoff = (now or datetime.now(UTC)) - timedelta(days=90)
        result = await session.execute(
            update(ConversationFeedback)
            .where(
                ConversationFeedback.comment.is_not(None),
                ConversationFeedback.submitted_at < cutoff,
            )
            .values(comment=None)
        )
        return result.rowcount or 0
