import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import Chatbot, Document

logger = logging.getLogger(__name__)


class ChatbotDeletionNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ChatbotDeletion:
    storage_keys: tuple[str, ...]


class ChatbotDeletionService:
    def __init__(self, settings: Settings) -> None:
        self.storage_path = settings.document_storage_path.resolve()

    async def delete_chatbot(
        self,
        session: AsyncSession,
        chatbot_id: UUID,
    ) -> ChatbotDeletion:
        chatbot = await session.scalar(
            select(Chatbot).where(Chatbot.id == chatbot_id).with_for_update()
        )
        if chatbot is None:
            raise ChatbotDeletionNotFoundError

        storage_keys = tuple(
            await session.scalars(
                select(Document.storage_key).where(Document.chatbot_id == chatbot_id)
            )
        )
        await session.delete(chatbot)
        await session.flush()
        return ChatbotDeletion(storage_keys=storage_keys)

    def clean_private_files(self, deletion: ChatbotDeletion) -> None:
        for storage_key in deletion.storage_keys:
            path = self._path_for_storage_key(storage_key)
            if path is None:
                logger.error(
                    "Ignored invalid private document storage key during cleanup"
                )
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError:
                logger.exception("Unable to remove an inaccessible private document")

    def _path_for_storage_key(self, storage_key: str) -> Path | None:
        filename = Path(storage_key).name
        if not filename or filename in {".", ".."}:
            return None
        path = (self.storage_path / filename).resolve()
        return path if path.parent == self.storage_path else None
