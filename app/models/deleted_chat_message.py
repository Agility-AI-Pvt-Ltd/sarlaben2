from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class DeletedChatMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "deleted_chat_messages"

    original_message_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        index=True,
    )
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    cattle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cattle.id", ondelete="CASCADE"),
        index=True,
    )
    farmer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("farmers.id", ondelete="CASCADE"),
        index=True,
    )
    message: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(String(16))
    original_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    original_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    purge_after: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
