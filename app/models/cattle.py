from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Cattle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cattle"

    farmer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("farmers.id", ondelete="CASCADE"),
        index=True,
    )
    cattle_tag: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    breed: Mapped[str | None] = mapped_column(String(120))
    sex: Mapped[str | None] = mapped_column(String(24))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    farmer = relationship("User", back_populates="cattle")
    sessions = relationship(
        "ChatSession", back_populates="cattle", cascade="all, delete-orphan"
    )
    memories = relationship(
        "CattleMemory", back_populates="cattle", cascade="all, delete-orphan"
    )
    call_logs = relationship(
        "CallLog", back_populates="cattle", cascade="all, delete-orphan"
    )
