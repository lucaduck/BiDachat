import asyncio
import sys
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select

from app.core.config import Settings
from app.database.session import Database
from app.models import Chatbot, Document, DocumentChunk, LlmModel, User
from app.services.rag_knowledge_service import (
    ChunkInput,
    ChunkValidationError,
    EmbeddingProfileError,
    RagKnowledgeService,
)


def _embedding(first: float, second: float = 0.0) -> list[float]:
    return [first, second, *([0.0] * 766)]


def test_embedding_profile_and_chunk_validation():
    with pytest.raises(EmbeddingProfileError):
        RagKnowledgeService(Settings(embedding_dimensions=1536))

    service = RagKnowledgeService(Settings())
    with pytest.raises(EmbeddingProfileError):
        service._validate_embedding([1.0])
    with pytest.raises(ChunkValidationError):
        service._validate_embedding([0.0] * 768)


@pytest.mark.integration
def test_atomic_publication_retry_profile_and_chatbot_isolation():
    settings = Settings()
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")

    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        runner.run(_exercise_rag_lifecycle(settings))


async def _exercise_rag_lifecycle(settings: Settings) -> None:
    database = Database.from_settings(settings)
    service = RagKnowledgeService(settings)
    user_id = uuid4()
    model_id = uuid4()
    chatbot_a_id = uuid4()
    chatbot_b_id = uuid4()
    document_a_id = uuid4()
    document_b_id = uuid4()

    try:
        async with database.session() as session:
            stale_user_ids = select(User.id).where(
                User.email.like("rag-%@bidachat.test")
            )
            await session.execute(
                delete(Chatbot).where(Chatbot.created_by.in_(stale_user_ids))
            )
            await session.execute(
                delete(User).where(User.email.like("rag-%@bidachat.test"))
            )
            await session.execute(
                delete(LlmModel).where(
                    LlmModel.provider == "test-provider",
                    LlmModel.model.like("rag-model-%"),
                )
            )
            session.add_all(
                [
                    User(
                        id=user_id,
                        email=f"rag-{user_id}@bidachat.test",
                        password_hash="integration-hash",
                    ),
                    LlmModel(
                        id=model_id,
                        provider="test-provider",
                        model=f"rag-model-{model_id}",
                    ),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    Chatbot(
                        id=chatbot_a_id,
                        created_by=user_id,
                        configured_llm_model_id=model_id,
                        name="Chatbot A",
                    ),
                    Chatbot(
                        id=chatbot_b_id,
                        created_by=user_id,
                        configured_llm_model_id=model_id,
                        name="Chatbot B",
                    ),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    Document(
                        id=document_a_id,
                        chatbot_id=chatbot_a_id,
                        original_filename="a.pdf",
                        storage_key=f"rag/{document_a_id}",
                        media_type="application/pdf",
                        size_bytes=100,
                    ),
                    Document(
                        id=document_b_id,
                        chatbot_id=chatbot_b_id,
                        original_filename="b.pdf",
                        storage_key=f"rag/{document_b_id}",
                        media_type="application/pdf",
                        size_bytes=100,
                    ),
                ]
            )
            await session.commit()

        async with database.session() as session:
            await service.begin_processing(
                session,
                document_id=document_a_id,
                chatbot_id=chatbot_a_id,
            )
            await session.commit()

        mixed_batch = [
            ChunkInput(0, "fragmento válido", _embedding(1.0)),
            ChunkInput(1, "fragmento inválido", [0.0] * 768),
        ]
        async with database.session() as session:
            with pytest.raises(ChunkValidationError):
                await service.publish_chunks(
                    session,
                    document_id=document_a_id,
                    chatbot_id=chatbot_a_id,
                    embedding_model=settings.embedding_model,
                    embedding_dimensions=settings.embedding_dimensions,
                    chunks=mixed_batch,
                )
            chunk_count = await session.scalar(
                select(func.count(DocumentChunk.id)).where(
                    DocumentChunk.document_id == document_a_id
                )
            )
            assert chunk_count == 0
            await service.mark_failed(
                session,
                document_id=document_a_id,
                chatbot_id=chatbot_a_id,
                error_code="INVALID_EMBEDDING",
            )
            await session.commit()

        async with database.session() as session:
            await service.begin_processing(
                session,
                document_id=document_a_id,
                chatbot_id=chatbot_a_id,
            )
            with pytest.raises(EmbeddingProfileError):
                await service.publish_chunks(
                    session,
                    document_id=document_a_id,
                    chatbot_id=chatbot_a_id,
                    embedding_model="incompatible-model",
                    embedding_dimensions=768,
                    chunks=[ChunkInput(0, "no publicado", _embedding(1.0))],
                )
            await service.publish_chunks(
                session,
                document_id=document_a_id,
                chatbot_id=chatbot_a_id,
                embedding_model=settings.embedding_model,
                embedding_dimensions=settings.embedding_dimensions,
                chunks=[
                    ChunkInput(0, "conocimiento exclusivo A", _embedding(1.0)),
                    ChunkInput(1, "contexto secundario A", _embedding(0.8, 0.2)),
                ],
            )
            await session.commit()

        async with database.session() as session:
            await service.begin_processing(
                session,
                document_id=document_b_id,
                chatbot_id=chatbot_b_id,
            )
            await service.publish_chunks(
                session,
                document_id=document_b_id,
                chatbot_id=chatbot_b_id,
                embedding_model=settings.embedding_model,
                embedding_dimensions=settings.embedding_dimensions,
                chunks=[ChunkInput(0, "conocimiento exclusivo B", _embedding(1.0))],
            )
            await session.commit()

        async with database.session() as session:
            with pytest.raises(EmbeddingProfileError):
                await service.retrieve_chunks(
                    session,
                    chatbot_id=chatbot_a_id,
                    embedding_model="incompatible-model",
                    embedding_dimensions=768,
                    query_embedding=_embedding(1.0),
                )
            retrieved = await service.retrieve_chunks(
                session,
                chatbot_id=chatbot_a_id,
                embedding_model=settings.embedding_model,
                embedding_dimensions=settings.embedding_dimensions,
                query_embedding=_embedding(1.0),
                top_k=10,
            )
            assert len(retrieved) == 2
            assert {chunk.document_id for chunk in retrieved} == {document_a_id}
            assert all(" B" not in chunk.content for chunk in retrieved)

            stored_indexes = await session.scalars(
                select(DocumentChunk.chunk_index)
                .where(DocumentChunk.document_id == document_a_id)
                .order_by(DocumentChunk.chunk_index)
            )
            assert list(stored_indexes) == [0, 1]
    finally:
        async with database.session() as session:
            await session.execute(delete(Chatbot).where(Chatbot.created_by == user_id))
            user = await session.get(User, user_id)
            if user is not None:
                await session.delete(user)
            llm_model = await session.get(LlmModel, model_id)
            if llm_model is not None:
                await session.delete(llm_model)
            await session.commit()
        await database.dispose()
