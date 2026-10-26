import csv
from io import BytesIO, StringIO
from pathlib import Path
from uuid import UUID
from zipfile import BadZipFile

from docx import Document as WordDocument
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.llm.provider import LlmProvider, ProviderConfigurationError, ProviderError
from app.models import Document
from app.services.rag_knowledge_service import ChunkInput, RagKnowledgeService

DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
IMAGE_MEDIA_TYPES = {"image/png", "image/jpeg", "image/webp"}
CSV_MEDIA_TYPES = {"text/csv", "application/csv", "application/vnd.ms-excel"}


class DocumentProcessingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.knowledge = RagKnowledgeService(settings)
        self.provider = LlmProvider(settings)

    async def process(
        self, session: AsyncSession, *, document: Document, chatbot_id: UUID
    ) -> Document:
        await self.knowledge.begin_processing(
            session, document_id=document.id, chatbot_id=chatbot_id
        )
        await session.commit()
        extracting_image = document.media_type in IMAGE_MEDIA_TYPES
        try:
            path = (
                self.settings.document_storage_path.resolve()
                / Path(document.storage_key).name
            )
            content = await self._extract_content(path, document.media_type)
            extracting_image = False
            chunks = RecursiveCharacterTextSplitter(
                chunk_size=1200, chunk_overlap=150
            ).split_text(content)
            if not chunks:
                raise ValueError("No readable text")
            vectors = await self.provider.embed_documents(chunks)
            embedded = [
                ChunkInput(
                    chunk_index=index,
                    content=chunk,
                    embedding=vectors[index],
                )
                for index, chunk in enumerate(chunks)
            ]
            result = await self.knowledge.publish_chunks(
                session,
                document_id=document.id,
                chatbot_id=chatbot_id,
                embedding_model=self.settings.embedding_model,
                embedding_dimensions=self.settings.embedding_dimensions,
                chunks=embedded,
            )
            await session.commit()
            return result
        except (ProviderError, ValueError, OSError) as exc:
            await session.rollback()
            if extracting_image and isinstance(exc, ProviderConfigurationError):
                error_code = "image_model_not_configured"
            elif extracting_image and isinstance(exc, ProviderError):
                error_code = "image_processing_failed"
            elif isinstance(exc, ProviderConfigurationError):
                error_code = "embedding_not_configured"
            elif isinstance(exc, ProviderError):
                error_code = "embedding_provider_failed"
            elif isinstance(exc, ValueError):
                error_code = "processing_failed"
            else:
                error_code = "file_read_failed"
            result = await self.knowledge.mark_failed(
                session,
                document_id=document.id,
                chatbot_id=chatbot_id,
                error_code=error_code,
            )
            await session.commit()
            return result

    async def _extract_content(self, path: Path, media_type: str) -> str:
        if media_type not in IMAGE_MEDIA_TYPES:
            return self._extract_text(path, media_type)
        model = self.settings.effective_vision_model
        if not model:
            raise ProviderConfigurationError(
                "VISION_MODEL is required for image sources"
            )
        description = await self.provider.answer(
            provider=self.settings.vision_provider,
            model=model,
            question=(
                "Transcribe all legible text and describe only visible facts in this "
                "image. Include chart titles, axis labels, legends, values, and "
                "table cells when readable. Do not infer missing values."
            ),
            instructions="Create a factual Spanish description for document retrieval.",
            context="",
            image=path.read_bytes(),
            image_mime_type=media_type,
        )
        if not description.strip():
            raise ValueError("No readable image content")
        return description

    @staticmethod
    def _extract_text(path: Path, media_type: str) -> str:
        content = path.read_bytes()
        try:
            if media_type == "application/pdf":
                text = "\n".join(
                    page.extract_text() or ""
                    for page in PdfReader(BytesIO(content)).pages
                )
            elif media_type == DOCX_MEDIA_TYPE:
                lines = []
                for item in WordDocument(BytesIO(content)).iter_inner_content():
                    if isinstance(item, Table):
                        rows = [
                            [cell.text.strip() for cell in row.cells]
                            for row in item.rows
                        ]
                        if rows:
                            headers = rows[0]
                            lines.append(" | ".join(headers))
                            for row in rows[1:]:
                                lines.append(
                                    " | ".join(
                                        f"{headers[index]}: {value}"
                                        if index < len(headers) and headers[index]
                                        else value
                                        for index, value in enumerate(row)
                                    )
                                )
                    elif item.text.strip():
                        lines.append(item.text.strip())
                text = "\n".join(lines)
            elif media_type in CSV_MEDIA_TYPES:
                decoded = content.decode("utf-8-sig")
                try:
                    dialect = csv.Sniffer().sniff(decoded[:4096], delimiters=",;\t")
                except csv.Error:
                    dialect = csv.excel
                reader = csv.reader(StringIO(decoded, newline=""), dialect=dialect)
                headers = next(reader, [])
                lines = []
                for row in reader:
                    if not any(value.strip() for value in row):
                        continue
                    cells = []
                    for index, value in enumerate(row):
                        column_name = (
                            headers[index].strip()
                            if index < len(headers) and headers[index].strip()
                            else f"column_{index + 1}"
                        )
                        cells.append(f"{column_name}: {value.strip()}")
                    lines.append(" | ".join(cells))
                text = "\n".join(lines)
            else:
                text = content.decode("utf-8")
        except (
            PdfReadError,
            PackageNotFoundError,
            BadZipFile,
            UnicodeDecodeError,
            csv.Error,
        ) as exc:
            raise ValueError("Document text cannot be extracted") from exc
        if not text.strip():
            raise ValueError("No readable text")
        return text
