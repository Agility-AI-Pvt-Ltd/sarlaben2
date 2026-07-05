from uuid import UUID

from fastapi import APIRouter, WebSocket

from app.database.session import SessionLocal
from app.services.websocket_service import WebSocketService
from app.websocket.connection_manager import connection_manager

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/cattle/{cattle_id}/human/{human_id}")
async def cattle_audio_socket(websocket: WebSocket, cattle_id: UUID, human_id: UUID):
    async with SessionLocal() as db:
        await WebSocketService(connection_manager, db).handle_audio_socket(
            websocket, cattle_id, human_id
        )


@router.websocket("/ai/cattle/{cattle_id}/human/{human_id}")
async def ai_cattle_audio_socket(websocket: WebSocket, cattle_id: UUID, human_id: UUID):
    async with SessionLocal() as db:
        await WebSocketService(connection_manager, db).handle_audio_socket(
            websocket, cattle_id, human_id, ai_mode=True
        )
