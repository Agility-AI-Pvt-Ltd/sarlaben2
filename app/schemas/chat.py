from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import CattleMemoryType, MessageType
from app.schemas.common import ORMModel, Timestamped


class ChatMessageCreate(BaseModel):
    session_id: UUID | None = None
    message: str = Field(min_length=1)


class AIMessageCreate(BaseModel):
    session_id: UUID
    context: str = Field(default="", max_length=4000)


class ChatMessageRead(Timestamped):
    id: UUID
    session_id: UUID
    cattle_id: UUID
    farmer_id: UUID
    message: str
    message_type: MessageType


class CattleMemoryCreate(BaseModel):
    cattle_data_text: str = Field(min_length=1)
    data_type_stored_by_ai: CattleMemoryType = CattleMemoryType.GENERAL
    source_message_id: UUID | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class CattleMemoryRead(ORMModel):
    id: UUID
    cattle_id: UUID
    source_message_id: UUID | None
    cattle_data_text: str
    data_type_stored_by_ai: CattleMemoryType
    confidence: float | None
    created_at: datetime
    updated_at: datetime
