"""Reprocess pending, failed or outdated documents with the configured profile."""

import asyncio

from sqlalchemy import or_, select

from app.core.config import get_settings
from app.database.session import Database
from app.models import Document
from app.services.document_processing_service import DocumentProcessingService


async def reindex_documents() -> None:
    settings = get_settings()
    database = Database.from_settings(settings)
    processor = DocumentProcessingService(settings)
    failed = 0
    try:
        async with database.session() as session:
            ids = list(
                await session.scalars(
                    select(Document.id).where(
                        Document.status.in_(["pending", "failed", "ready"]),
                        or_(
                            Document.status != "ready",
                            Document.embedding_model != settings.embedding_model,
                            Document.embedding_dimensions
                            != settings.embedding_dimensions,
                        ),
                    )
                )
            )
        for document_id in ids:
            async with database.session() as session:
                document = await session.scalar(
                    select(Document).where(Document.id == document_id).with_for_update()
                )
                if document is None or document.status == "processing":
                    continue
                if document.status == "ready":
                    if (
                        document.embedding_model == settings.embedding_model
                        and document.embedding_dimensions
                        == settings.embedding_dimensions
                    ):
                        continue
                    document.status = "pending"
                chatbot_id = document.chatbot_id
                result = await processor.process(
                    session, document=document, chatbot_id=chatbot_id
                )
                print(f"{document_id}: {result.status}", flush=True)
                failed += result.status != "ready"
        if failed:
            raise RuntimeError(f"{failed} documents failed; inspect their error codes")
    finally:
        await database.dispose()


if __name__ == "__main__":
    asyncio.run(reindex_documents())
