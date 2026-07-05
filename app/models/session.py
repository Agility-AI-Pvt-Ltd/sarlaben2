from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import SessionStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChatSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_sessions"

    cattle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cattle.id"), index=True
    )
    farmer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("farmers.id"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(24), default=SessionStatus.OPEN.value)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    cattle = relationship("Cattle", back_populates="sessions")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )
