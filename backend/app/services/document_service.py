from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4
from zipfile import BadZipFile, ZipFile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import Chatbot, Document

ALLOWED_DOCUMENT_TYPES = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
    ".txt": {"text/plain"},
    ".csv": {"text/csv", "application/csv", "application/vnd.ms-excel"},
}


class ChatbotDocumentNotFoundError(Exception):
    pass


class DocumentUploadValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class UploadDocument:
    filename: str | None
    media_type: str | None
    content: bytes


class DocumentService:
    def __init__(self, settings: Settings) -> None:
        self.storage_path = settings.document_storage_path.resolve()
        self.max_size_bytes = settings.document_max_size_bytes

    async def list_documents(
        self,
        session: AsyncSession,
        chatbot_id: UUID,
    ) -> list[Document]:
        await self._require_chatbot(session, chatbot_id)
        documents = await session.scalars(
            select(Document)
            .where(Document.chatbot_id == chatbot_id)
            .order_by(Document.created_at, Document.id)
        )
        return list(documents)

    async def upload_document(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        upload: UploadDocument,
    ) -> Document:
        await self._require_chatbot(session, chatbot_id)
        filename, extension, media_type = self._validate_upload(upload)
        document_id = uuid4()
        storage_key = f"documents/{document_id}{extension}"
        destination = self.storage_path / f"{document_id}{extension}"
        self._store_file(destination, upload.content)

        try:
            document = Document(
                id=document_id,
                chatbot_id=chatbot_id,
                original_filename=filename,
                storage_key=storage_key,
                media_type=media_type,
                size_bytes=len(upload.content),
            )
            session.add(document)
            await session.flush()
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return document

    async def _require_chatbot(
        self,
        session: AsyncSession,
        chatbot_id: UUID,
    ) -> None:
        chatbot = await session.scalar(
            select(Chatbot)
            .where(Chatbot.id == chatbot_id)
            .with_for_update(key_share=True)
        )
        if chatbot is None:
            raise ChatbotDocumentNotFoundError

    def _validate_upload(self, upload: UploadDocument) -> tuple[str, str, str]:
        if upload.filename is None:
            raise DocumentUploadValidationError("A filename is required")
        filename = Path(upload.filename).name.strip()
        if not filename or len(filename) > 255:
            raise DocumentUploadValidationError("Invalid filename")
        extension = Path(filename).suffix.lower()
        allowed_media_types = ALLOWED_DOCUMENT_TYPES.get(extension)
        media_type = (upload.media_type or "").lower().strip()
        if allowed_media_types is None or media_type not in allowed_media_types:
            raise DocumentUploadValidationError("Unsupported document type")
        if not upload.content:
            raise DocumentUploadValidationError("Document cannot be empty")
        if len(upload.content) > self.max_size_bytes:
            raise DocumentUploadValidationError("Document exceeds the maximum size")
        self._validate_content(extension, upload.content)
        return filename, extension, media_type

    def _validate_content(self, extension: str, content: bytes) -> None:
        if extension == ".pdf" and not content.startswith(b"%PDF-"):
            raise DocumentUploadValidationError("Invalid PDF content")
        if extension == ".docx":
            try:
                with ZipFile(BytesIO(content)) as archive:
                    if "[Content_Types].xml" not in archive.namelist():
                        raise DocumentUploadValidationError("Invalid DOCX content")
            except BadZipFile as exc:
                raise DocumentUploadValidationError("Invalid DOCX content") from exc
        if extension in {".txt", ".csv"}:
            try:
                content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise DocumentUploadValidationError(
                    "Text files must use UTF-8"
                ) from exc

    def _store_file(self, destination: Path, content: bytes) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(f"{destination.suffix}.uploading")
        try:
            temporary.write_bytes(content)
            temporary.replace(destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
