from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.schemas.common import Timestamped

E164PhoneNumber = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^\+[1-9]\d{7,14}$",
    ),
]


class UserCreate(BaseModel):
    phone_number: E164PhoneNumber
    full_name: str | None = Field(default=None, max_length=120)
    preferred_language: str = Field(default="en-IN", min_length=2, max_length=16)

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class UserRead(Timestamped):
    id: UUID
    phone_number: str
    full_name: str | None
    profile_image_uri: str | None
    preferred_language: str
    is_phone_verified: bool
    phone_verified_at: datetime | None
    is_active: bool


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    profile_image_uri: str | None = Field(default=None, max_length=2048)
    preferred_language: Literal["en-IN", "hi-IN"] | None = None

    @field_validator("full_name", "profile_image_uri")
    @classmethod
    def clean_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class OTPRequest(BaseModel):
    phone_number: E164PhoneNumber


class OTPRequestResponse(BaseModel):
    phone_number: str
    status: str
    account_exists: bool
    requires_name: bool


class OTPVerifyRequest(UserCreate):
    code: str = Field(pattern=r"^\d{4,10}$")


class OTPVerifyResponse(BaseModel):
    verified: bool
    user: UserRead
