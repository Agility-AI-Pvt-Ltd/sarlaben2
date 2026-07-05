from pydantic import BaseModel, Field


class AudioChunkMetadata(BaseModel):
    sequence: int = Field(ge=0)
    sample_rate: int = Field(default=16000, ge=8000)
    mime_type: str = "audio/webm"
    client_vad: bool = True
