from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import Timestamped


class PushTokenCreate(BaseModel):
    farmer_id: UUID
    expo_push_token: str = Field(min_length=20, max_length=255)
    platform: str | None = Field(default=None, max_length=24)
    device_id: str | None = Field(default=None, max_length=128)

    @field_validator("expo_push_token")
    @classmethod
    def validate_push_token(cls, value: str) -> str:
        token = value.strip()
        if not token:
            raise ValueError("Invalid push token")
        return token


class PushTokenRead(Timestamped):
    id: UUID
    farmer_id: UUID
    expo_push_token: str
    platform: str | None
    device_id: str | None
