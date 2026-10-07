from datetime import datetime

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    window_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
