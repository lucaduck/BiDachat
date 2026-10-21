import asyncio
import logging

from app.core.config import Settings
from app.database.session import Database
from app.services.conversation_memory_service import ConversationMemoryService

logger = logging.getLogger(__name__)


async def run_conversation_cleanup(database: Database, settings: Settings) -> None:
    while True:
        try:
            async with database.session() as session:
                removed = await ConversationMemoryService(settings).cleanup_expired(
                    session
                )
                await session.commit()
            logger.info(
                "Expired conversation cleanup removed %s conversations", removed
            )
        except Exception:
            logger.exception("Expired conversation cleanup failed; it will be retried")
        await asyncio.sleep(settings.conversation_cleanup_interval_minutes * 60)
