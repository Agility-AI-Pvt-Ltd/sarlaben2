from enum import StrEnum


class MessageType(StrEnum):
    HUMAN = "human"
    AI = "ai"


class CattleMemoryType(StrEnum):
    MEDICAL = "medical"
    HEALTH = "health"
    FEEDING = "feeding"
    BREEDING = "breeding"
    MILK = "milk"
    MEDICINE = "medicine"
    GENERAL = "general"


class SessionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class WebSocketEvent(StrEnum):
    CONNECTED = "connected"
    AUDIO_CHUNK = "audio.chunk"
    VAD_SPEECH_STARTED = "client.vad.speech_started"
    VAD_SPEECH_ENDED = "client.vad.speech_ended"
    TRANSCRIPT = "transcript"
    AI_MESSAGE = "ai.message"
    ERROR = "error"
