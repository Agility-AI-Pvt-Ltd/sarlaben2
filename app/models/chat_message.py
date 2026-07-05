from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import MessageType
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"

    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("chat_sessions.id"), index=True
    )
    cattle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cattle.id"), index=True
    )
    farmer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("farmers.id"), index=True
    )
    message: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(
        String(16), default=MessageType.HUMAN.value
    )

    session = relationship("ChatSession", back_populates="messages")
