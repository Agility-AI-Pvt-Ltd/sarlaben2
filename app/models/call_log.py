from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CallLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "call_logs"

    cattle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cattle.id"), index=True
    )
    farmer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("farmers.id"), index=True
    )
    session_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("chat_sessions.id")
    )
    call_logs: Mapped[str | None] = mapped_column(Text)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    cattle = relationship("Cattle", back_populates="call_logs")
