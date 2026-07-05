from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "farmers"

    full_name: Mapped[str | None] = mapped_column(String(120))
    phone_number: Mapped[str] = mapped_column(String(32), unique=True)
    preferred_language: Mapped[str] = mapped_column(String(16), default="en-IN")
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    cattle = relationship(
        "Cattle", back_populates="farmer", cascade="all, delete-orphan"
    )
