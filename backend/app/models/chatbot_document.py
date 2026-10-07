from uuid import UUID

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ChatbotDocument(Base):
    __tablename__ = "chatbot_documents"
    __table_args__ = (PrimaryKeyConstraint("chatbot_id", "document_id"),)

    chatbot_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("chatbots.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
