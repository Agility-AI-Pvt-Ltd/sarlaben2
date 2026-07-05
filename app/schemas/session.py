from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.constants import SessionStatus
from app.schemas.common import Timestamped


class SessionCreate(BaseModel):
    cattle_id: UUID
    farmer_id: UUID
    title: str | None = None


class SessionRead(Timestamped):
    id: UUID
    cattle_id: UUID
    farmer_id: UUID
    title: str | None
    status: SessionStatus
    closed_at: datetime | None
