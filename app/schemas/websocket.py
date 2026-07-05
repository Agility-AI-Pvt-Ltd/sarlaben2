from uuid import UUID

from pydantic import BaseModel


class WebSocketEnvelope(BaseModel):
    event: str
    cattle_id: UUID
    human_id: UUID
    payload: dict = {}
