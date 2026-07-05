from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class PushToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "push_tokens"

    farmer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("farmers.id", ondelete="CASCADE"),
        index=True,
    )
    expo_push_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    platform: Mapped[str | None] = mapped_column(String(24))
    device_id: Mapped[str | None] = mapped_column(String(128))
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    farmer = relationship("User", back_populates="push_tokens")
