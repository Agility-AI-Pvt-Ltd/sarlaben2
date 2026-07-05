from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import Timestamped


class CallLogCreate(BaseModel):
    cattle_id: UUID
    farmer_id: UUID
    session_id: UUID | None = None
    call_logs: str | None = None
    duration_seconds: int = Field(default=0, ge=0)
    started_at: datetime | None = None
    ended_at: datetime | None = None


class CallLogRead(Timestamped):
    id: UUID
    cattle_id: UUID
    farmer_id: UUID
    session_id: UUID | None
    call_logs: str | None
    duration_seconds: int
    started_at: datetime | None
    ended_at: datetime | None
