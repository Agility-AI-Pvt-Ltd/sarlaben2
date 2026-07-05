import json
from uuid import UUID

from fastapi import WebSocket

from app.core.constants import WebSocketEvent
from app.websocket.connection_manager import ConnectionManager


class WebSocketService:
    def __init__(self, manager: ConnectionManager) -> None:
        self.manager = manager

    async def handle_audio_socket(
        self,
        websocket: WebSocket,
        cattle_id: UUID,
        human_id: UUID,
        ai_mode: bool = False,
    ) -> None:
        await self.manager.connect(cattle_id, human_id, websocket)
        await websocket.send_json(
            {
                "event": WebSocketEvent.CONNECTED.value,
                "cattle_id": str(cattle_id),
                "human_id": str(human_id),
                "payload": {"ai_mode": ai_mode, "vad": "client-side"},
            }
        )
        try:
            while True:
                message = await websocket.receive()
                if "bytes" in message and message["bytes"] is not None:
                    await self._handle_audio_chunk(websocket, message["bytes"])
                elif "text" in message and message["text"] is not None:
                    await self._handle_text_event(websocket, message["text"])
        finally:
            self.manager.disconnect(cattle_id, human_id, websocket)

    async def _handle_audio_chunk(self, websocket: WebSocket, chunk: bytes) -> None:
        await websocket.send_json(
            {
                "event": WebSocketEvent.AUDIO_CHUNK.value,
                "payload": {"bytes_received": len(chunk)},
            }
        )

    async def _handle_text_event(self, websocket: WebSocket, text: str) -> None:
        try:
            event = json.loads(text)
        except json.JSONDecodeError:
            event = {"event": "text", "payload": {"text": text}}
        await websocket.send_json({"event": "ack", "payload": event})
