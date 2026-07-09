import base64
import binascii
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.constants import CattleMemoryType, MessageType
from app.schemas.common import ORMModel, Timestamped


class ChatMessageCreate(BaseModel):
    session_id: UUID | None = None
    message: str = Field(min_length=1)


class ImageMessageCreate(BaseModel):
    session_id: UUID | None = None
    image_data_url: str = Field(min_length=32, max_length=7_000_000)

    @field_validator("image_data_url")
    @classmethod
    def validate_image_data_url(cls, value: str) -> str:
        prefixes = (
            "data:image/jpeg;base64,",
            "data:image/png;base64,",
            "data:image/webp;base64,",
        )
        if not value.startswith(prefixes):
            raise ValueError("Only JPEG, PNG, or WebP images are supported")

        encoded_image = value.split(",", 1)[1]
        try:
            image_bytes = base64.b64decode(encoded_image, validate=True)
        except (ValueError, binascii.Error) as error:
            raise ValueError("Image data is not valid base64") from error

        if len(image_bytes) > 5_000_000:
            raise ValueError("Image must be 5 MB or smaller")
        return value


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


class HumanAIMessageRead(BaseModel):
    human_message: ChatMessageRead
    ai_message: ChatMessageRead


class ClearChatResponse(BaseModel):
    archived_messages: int
    purge_after: datetime | None


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
