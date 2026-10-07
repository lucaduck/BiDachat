from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    chatbot_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("chatbots.id", ondelete="CASCADE"),
        nullable=False,
    )
    executed_llm_model_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("llm_models.id", ondelete="RESTRICT"),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text)
    has_image: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="processing",
    )
    error_code: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_time_ms: Mapped[int | None] = mapped_column(BigInteger)
