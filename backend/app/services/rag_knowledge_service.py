from dataclasses import dataclass
from datetime import UTC, datetime
from math import fsum, isfinite
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import DEFAULT_EMBEDDING_DIMENSIONS, Settings
from app.models import ChatbotDocument, Document, DocumentChunk


class DocumentNotFoundError(Exception):
    pass


class DocumentStateError(Exception):
    pass


class EmbeddingProfileError(Exception):
    pass


class ChunkValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ChunkInput:
    chunk_index: int
    content: str
    embedding: list[float]
    page_number: int | None = None


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    content: str
    page_number: int | None
    distance: float


class RagKnowledgeService:
    def __init__(self, settings: Settings) -> None:
        self.embedding_model = settings.embedding_model.strip()
        self.embedding_dimensions = settings.embedding_dimensions
        if not self.embedding_model:
            raise EmbeddingProfileError("Embedding model cannot be empty")
        if self.embedding_dimensions != DEFAULT_EMBEDDING_DIMENSIONS:
            raise EmbeddingProfileError(
                "Configured embedding dimensions do not match the database schema"
            )

    async def begin_processing(
        self,
        session: AsyncSession,
        *,
        document_id: UUID,
        chatbot_id: UUID,
    ) -> Document:
        async with session.begin_nested():
            document = await self._get_locked_document(
                session,
                document_id=document_id,
                chatbot_id=chatbot_id,
            )
            if document.status not in {"pending", "failed"}:
                raise DocumentStateError(
                    "Only pending or failed documents can start processing"
                )

            await session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )
            document.status = "processing"
            document.error_code = None
            document.embedding_model = self.embedding_model
            document.embedding_dimensions = self.embedding_dimensions
            document.processed_at = None
            document.updated_at = datetime.now(UTC)
            await session.flush()
        return document

    async def publish_chunks(
        self,
        session: AsyncSession,
        *,
        document_id: UUID,
        chatbot_id: UUID,
        embedding_model: str,
        embedding_dimensions: int,
        chunks: list[ChunkInput],
    ) -> Document:
        self._require_profile(embedding_model, embedding_dimensions)
        normalized_chunks = self._validate_chunks(chunks)

        async with session.begin_nested():
            document = await self._get_locked_document(
                session,
                document_id=document_id,
                chatbot_id=chatbot_id,
            )
            if document.status != "processing":
                raise DocumentStateError("Only processing documents can publish chunks")
            if (
                document.embedding_model != self.embedding_model
                or document.embedding_dimensions != self.embedding_dimensions
            ):
                raise EmbeddingProfileError(
                    "Document profile does not match the configured embedding profile"
                )

            await session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )
            session.add_all(
                [
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        page_number=chunk.page_number,
                        embedding=chunk.embedding,
                    )
                    for chunk in normalized_chunks
                ]
            )
            now = datetime.now(UTC)
            document.status = "ready"
            document.error_code = None
            document.processed_at = now
            document.updated_at = now
            await session.flush()
        return document

    async def mark_failed(
        self,
        session: AsyncSession,
        *,
        document_id: UUID,
        chatbot_id: UUID,
        error_code: str,
    ) -> Document:
        normalized_error = error_code.strip()
        if not normalized_error:
            raise ValueError("Error code cannot be empty")

        async with session.begin_nested():
            document = await self._get_locked_document(
                session,
                document_id=document_id,
                chatbot_id=chatbot_id,
            )
            if document.status != "processing":
                raise DocumentStateError(
                    "Only processing documents can be marked as failed"
                )
            await session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )
            document.status = "failed"
            document.error_code = normalized_error
            document.processed_at = None
            document.updated_at = datetime.now(UTC)
            await session.flush()
        return document

    async def retrieve_chunks(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        embedding_model: str,
        embedding_dimensions: int,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        self._require_profile(embedding_model, embedding_dimensions)
        normalized_embedding = self._validate_embedding(query_embedding)
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50")

        distance = DocumentChunk.embedding.cosine_distance(normalized_embedding).label(
            "distance"
        )
        result = await session.execute(
            select(
                DocumentChunk.id,
                DocumentChunk.document_id,
                DocumentChunk.content,
                DocumentChunk.page_number,
                distance,
            )
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(ChatbotDocument, ChatbotDocument.document_id == Document.id)
            .where(
                ChatbotDocument.chatbot_id == chatbot_id,
                Document.status == "ready",
                Document.embedding_model == self.embedding_model,
                Document.embedding_dimensions == self.embedding_dimensions,
            )
            .order_by(distance, DocumentChunk.id)
            .limit(top_k)
        )
        return [
            RetrievedChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                content=content,
                page_number=page_number,
                distance=float(chunk_distance),
            )
            for chunk_id, document_id, content, page_number, chunk_distance in result
        ]

    async def _get_locked_document(
        self,
        session: AsyncSession,
        *,
        document_id: UUID,
        chatbot_id: UUID,
    ) -> Document:
        document = await session.scalar(
            select(Document)
            .where(
                Document.id == document_id,
                Document.chatbot_id == chatbot_id,
            )
            .with_for_update()
        )
        if document is None:
            raise DocumentNotFoundError
        return document

    def _require_profile(self, model: str, dimensions: int) -> None:
        if (
            model.strip() != self.embedding_model
            or dimensions != self.embedding_dimensions
        ):
            raise EmbeddingProfileError(
                "Embedding profile does not match the configured profile"
            )

    def _validate_chunks(self, chunks: list[ChunkInput]) -> list[ChunkInput]:
        if not chunks:
            raise ChunkValidationError("At least one chunk is required")

        indexes: set[int] = set()
        normalized: list[ChunkInput] = []
        for chunk in chunks:
            if chunk.chunk_index < 0 or chunk.chunk_index in indexes:
                raise ChunkValidationError(
                    "Chunk indexes must be unique and nonnegative"
                )
            content = chunk.content.strip()
            if not content:
                raise ChunkValidationError("Chunk content cannot be empty")
            if chunk.page_number is not None and chunk.page_number <= 0:
                raise ChunkValidationError("Page number must be positive")
            indexes.add(chunk.chunk_index)
            normalized.append(
                ChunkInput(
                    chunk_index=chunk.chunk_index,
                    content=content,
                    page_number=chunk.page_number,
                    embedding=self._validate_embedding(chunk.embedding),
                )
            )
        return normalized

    def _validate_embedding(self, embedding: list[float]) -> list[float]:
        if len(embedding) != self.embedding_dimensions:
            raise EmbeddingProfileError(
                "Embedding dimensions do not match the configured profile"
            )
        normalized = [float(value) for value in embedding]
        if not all(isfinite(value) for value in normalized):
            raise ChunkValidationError("Embedding values must be finite")
        if fsum(value * value for value in normalized) == 0:
            raise ChunkValidationError("Embedding norm must be greater than zero")
        return normalized
