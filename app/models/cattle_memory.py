from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CattleMemoryType
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CattleMemory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cattle_memories"

    cattle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cattle.id"), index=True
    )
    source_message_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_messages.id"),
        nullable=True,
    )
    cattle_data_text: Mapped[str] = mapped_column(Text)
    data_type_stored_by_ai: Mapped[str] = mapped_column(
        String(48), default=CattleMemoryType.GENERAL.value
    )
    confidence: Mapped[float | None] = mapped_column(Float)

    cattle = relationship("Cattle", back_populates="memories")
