from app.core.constants import WebSocketEvent

CLIENT_AUDIO_EVENTS = {
    WebSocketEvent.VAD_SPEECH_STARTED.value,
    WebSocketEvent.VAD_SPEECH_ENDED.value,
    WebSocketEvent.AUDIO_CHUNK.value,
}
