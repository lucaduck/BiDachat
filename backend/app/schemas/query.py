import base64
import binascii
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    page_context: str | None = Field(default=None, max_length=6000)
    image_base64: str | None = Field(default=None, max_length=5_600_000)
    image_mime_type: str | None = None

    @model_validator(mode="after")
    def validate_image(self) -> "QueryRequest":
        if not self.question.strip():
            raise ValueError("Question must not be blank")
        if self.page_context is not None:
            self.page_context = " ".join(self.page_context.split()) or None
        if self.image_base64 is None:
            if self.image_mime_type is not None:
                raise ValueError("Image MIME type requires image data")
            return self
        if self.image_mime_type not in {"image/png", "image/jpeg", "image/webp"}:
            raise ValueError("Unsupported image type")
        try:
            image = base64.b64decode(self.image_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Invalid image") from exc
        if not image or len(image) > 4 * 1024 * 1024:
            raise ValueError("Image size must be between 1 byte and 4 MiB")
        signatures = {
            "image/png": image.startswith(b"\x89PNG\r\n\x1a\n"),
            "image/jpeg": image.startswith(b"\xff\xd8\xff"),
            "image/webp": image.startswith(b"RIFF") and image[8:12] == b"WEBP",
        }
        if not signatures[self.image_mime_type]:
            raise ValueError("Image content does not match its type")
        return self

    def image_bytes(self) -> bytes | None:
        return base64.b64decode(self.image_base64) if self.image_base64 else None


class QueryResponse(BaseModel):
    id: UUID
    answer: str
    response_time_ms: int
    completed_at: datetime
