from datetime import date
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field, field_validator

from app.schemas.common import Timestamped


class CattleCreate(BaseModel):
    farmer_id: UUID
    cattle_tag: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("cattle_id", "cattle_tag"),
    )
    name: str = Field(min_length=1, max_length=120)
    breed: str | None = None
    sex: str | None = None
    date_of_birth: date | None = None
    notes: str | None = None

    @field_validator("cattle_tag", mode="before")
    @classmethod
    def empty_cattle_id_is_missing(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class CattleUpdate(BaseModel):
    cattle_tag: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    breed: str | None = None
    sex: str | None = None
    date_of_birth: date | None = None
    notes: str | None = None


class CattleRead(Timestamped):
    id: UUID
    farmer_id: UUID
    cattle_tag: str
    name: str
    breed: str | None
    sex: str | None
    date_of_birth: date | None
    notes: str | None
