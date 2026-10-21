from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import Conversation, ConversationMessage, Query


class ConversationMemoryService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def resolve(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        requested_id: UUID | None,
        origin: str | None,
        identity_hash: str | None = None,
        now: datetime | None = None,
    ) -> Conversation:
        current_time = now or datetime.now(UTC)
        normalized_origin = normalize_origin(origin)
        if requested_id is not None:
            conversation = await session.scalar(
                select(Conversation)
                .where(Conversation.id == requested_id)
                .with_for_update()
            )
            if (
                conversation is not None
                and conversation.chatbot_id == chatbot_id
                and conversation.origin == normalized_origin
                and conversation.identity_hash == identity_hash
                and conversation.expires_at > current_time
            ):
                conversation.last_active_at = current_time
                conversation.expires_at = current_time + self._ttl
                await session.flush()
                return conversation

        conversation = Conversation(
            id=uuid4(),
            chatbot_id=chatbot_id,
            origin=normalized_origin,
            identity_hash=identity_hash,
            created_at=current_time,
            last_active_at=current_time,
            expires_at=current_time + self._ttl,
        )
        session.add(conversation)
        await session.flush()
        return conversation

    async def recent_messages(
        self,
        session: AsyncSession,
        *,
        conversation_id: UUID,
    ) -> list[tuple[str, str]]:
        result = await session.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(
                ConversationMessage.created_at.desc(),
                ConversationMessage.id.desc(),
            )
            .limit(self.settings.conversation_max_turns * 2)
        )
        newest_first = list(result)
        selected_turns: list[list[ConversationMessage]] = []
        character_count = 0
        for index in range(0, len(newest_first), 2):
            turn = newest_first[index : index + 2]
            if len(turn) != 2 or turn[0].query_id != turn[1].query_id:
                continue
            next_count = character_count + sum(len(message.content) for message in turn)
            if next_count > self.settings.conversation_max_chars:
                break
            selected_turns.append(turn)
            character_count = next_count
        selected = [
            message for turn in reversed(selected_turns) for message in reversed(turn)
        ]
        return [(message.role, message.content) for message in selected]

    async def save_successful_turn(
        self,
        session: AsyncSession,
        *,
        conversation_id: UUID,
        query: Query,
    ) -> None:
        if query.answer is None:
            raise ValueError("Completed query requires an answer")
        session.add_all(
            [
                ConversationMessage(
                    id=uuid4(),
                    conversation_id=conversation_id,
                    query_id=query.id,
                    role="user",
                    content=query.question,
                    created_at=query.received_at,
                ),
                ConversationMessage(
                    id=uuid4(),
                    conversation_id=conversation_id,
                    query_id=query.id,
                    role="assistant",
                    content=query.answer,
                    created_at=query.completed_at or datetime.now(UTC),
                ),
            ]
        )
        await session.flush()

    async def cleanup_expired(
        self,
        session: AsyncSession,
        *,
        now: datetime | None = None,
    ) -> int:
        result = await session.execute(
            delete(Conversation).where(
                Conversation.expires_at <= (now or datetime.now(UTC))
            )
        )
        return result.rowcount or 0

    @property
    def _ttl(self) -> timedelta:
        return timedelta(hours=self.settings.conversation_ttl_hours)


def normalize_origin(origin: str | None) -> str:
    if not origin:
        return "same-origin"
    parsed = urlsplit(origin)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        return "same-origin"
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
