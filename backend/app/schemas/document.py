from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chatbot_id: UUID
    original_filename: str
    media_type: str
    size_bytes: int
    status: str
    error_code: str | None
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None
