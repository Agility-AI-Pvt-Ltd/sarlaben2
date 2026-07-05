import base64
import json
from datetime import UTC, datetime
from uuid import UUID

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import WebSocketEvent
from app.core.exceptions import AppError
from app.schemas.call import CallLogCreate
from app.schemas.chat import AIMessageCreate, ChatMessageCreate
from app.services.call_service import CallService
from app.services.chat_service import ChatService
from app.ai.speech.voice_pipeline import VoicePipeline
from app.websocket.connection_manager import ConnectionManager


class WebSocketService:
    def __init__(self, manager: ConnectionManager, db: AsyncSession) -> None:
        self.manager = manager
        self.db = db
        self.voice_pipeline = VoicePipeline()
        self.session_id: UUID | None = None
        self.cattle_name: str | None = None
        self.started_at: datetime | None = None
        self.turn_count = 0
        self.call_transcript: list[str] = []
        self.call_log_saved = False

    async def handle_audio_socket(
        self,
        websocket: WebSocket,
        cattle_id: UUID,
        human_id: UUID,
        ai_mode: bool = False,
    ) -> None:
        await self.manager.connect(cattle_id, human_id, websocket)
        self.started_at = datetime.now(UTC)
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
                    await self._handle_audio_utterance(
                        websocket, cattle_id, human_id, message["bytes"]
                    )
                elif "text" in message and message["text"] is not None:
                    should_close = await self._handle_text_event(
                        websocket, cattle_id, human_id, message["text"]
                    )
                    if should_close:
                        break
        finally:
            if not self.call_log_saved and (self.turn_count > 0 or self.session_id):
                await self._save_call_log(cattle_id, human_id)
            self.manager.disconnect(cattle_id, human_id, websocket)

    async def _handle_audio_utterance(
        self, websocket: WebSocket, cattle_id: UUID, human_id: UUID, audio: bytes
    ) -> None:
        await websocket.send_json(
            {
                "event": WebSocketEvent.AUDIO_CHUNK.value,
                "payload": {"bytes_received": len(audio), "status": "processing"},
            }
        )
        try:
            transcript = await self.voice_pipeline.transcribe(audio)
            if not transcript:
                await websocket.send_json(
                    {
                        "event": WebSocketEvent.ERROR.value,
                        "payload": {"message": "No speech was detected."},
                    }
                )
                return

            chat_service = ChatService(self.db)
            human_message = await chat_service.add_human_message(
                cattle_id,
                human_id,
                ChatMessageCreate(session_id=self.session_id, message=transcript),
            )
            self.session_id = human_message.session_id
            self.call_transcript.append(f"Farmer: {transcript}")
            await websocket.send_json(
                {
                    "event": WebSocketEvent.TRANSCRIPT.value,
                    "payload": {"message": self._message_payload(human_message)},
                }
            )

            context = self._build_call_context(cattle_id)
            ai_message = await chat_service.add_ai_message(
                cattle_id,
                human_id,
                AIMessageCreate(session_id=human_message.session_id, context=context),
            )
            self.call_transcript.append(f"CowX AI: {ai_message.message}")
            audio_bytes = await self.voice_pipeline.synthesize(ai_message.message)
            self.turn_count += 1
            await websocket.send_json(
                {
                    "event": WebSocketEvent.AI_MESSAGE.value,
                    "payload": {
                        "message": self._message_payload(ai_message),
                        "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
                        "audio_codec": "mp3",
                    },
                }
            )
        except AppError as exc:
            await websocket.send_json(
                {
                    "event": WebSocketEvent.ERROR.value,
                    "payload": {"message": exc.message},
                }
            )

    async def _handle_text_event(
        self, websocket: WebSocket, cattle_id: UUID, human_id: UUID, text: str
    ) -> bool:
        try:
            event = json.loads(text)
        except json.JSONDecodeError:
            event = {"event": "text", "payload": {"text": text}}
        event_name = event.get("event")
        payload = event.get("payload") or {}
        if event_name == "call.setup":
            self.cattle_name = payload.get("cattle_name")
            session_id = payload.get("session_id")
            self.session_id = UUID(session_id) if session_id else None
        elif event_name == "call.end":
            await self._save_call_log(cattle_id, human_id)
            await websocket.send_json(
                {
                    "event": "call.ended",
                    "payload": {
                        "session_id": str(self.session_id) if self.session_id else None,
                        "turn_count": self.turn_count,
                    },
                }
            )
            return True
        await websocket.send_json({"event": "ack", "payload": event})
        return False

    async def _save_call_log(self, cattle_id: UUID, human_id: UUID) -> None:
        if self.call_log_saved:
            return
        self.call_log_saved = True
        started_at = self.started_at or datetime.now(UTC)
        ended_at = datetime.now(UTC)
        await CallService(self.db).create_call_log(
            CallLogCreate(
                cattle_id=cattle_id,
                farmer_id=human_id,
                session_id=self.session_id,
                call_logs="\n".join(self.call_transcript) or None,
                duration_seconds=max(0, round((ended_at - started_at).total_seconds())),
                started_at=started_at,
                ended_at=ended_at,
            )
        )

    def _build_call_context(self, cattle_id: UUID) -> str:
        cattle_label = self.cattle_name or "this cattle"
        return (
            "This request came from a live voice call. "
            f"The farmer is asking about cattle name: {cattle_label}; "
            f"cattle id: {cattle_id}. Keep replies concise and spoken-friendly."
        )

    def _message_payload(self, message) -> dict[str, str]:
        return {
            "id": str(message.id),
            "session_id": str(message.session_id),
            "cattle_id": str(message.cattle_id),
            "farmer_id": str(message.farmer_id),
            "message": message.message,
            "message_type": message.message_type,
            "created_at": message.created_at.isoformat(),
            "updated_at": message.updated_at.isoformat(),
        }
