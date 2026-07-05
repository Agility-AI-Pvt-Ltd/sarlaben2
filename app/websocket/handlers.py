from uuid import UUID

from fastapi import WebSocket

from app.services.websocket_service import WebSocketService
from app.websocket.connection_manager import connection_manager


async def handle_cattle_audio(
    websocket: WebSocket, cattle_id: UUID, human_id: UUID, ai_mode: bool = False
) -> None:
    await WebSocketService(connection_manager).handle_audio_socket(
        websocket, cattle_id, human_id, ai_mode=ai_mode
    )
