import asyncio

from app.core.config import get_settings
from app.database.session import Database
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.satisfaction_service import SatisfactionService


async def cleanup() -> int:
    settings = get_settings()
    database = Database.from_settings(settings)
    try:
        async with database.session() as session:
            removed = await ConversationMemoryService(settings).cleanup_expired(session)
            await SatisfactionService().redact_expired_comments(session)
            await session.commit()
            return removed
    finally:
        await database.dispose()


if __name__ == "__main__":
    removed_count = asyncio.run(cleanup())
    print(f"Removed expired conversations: {removed_count}")
