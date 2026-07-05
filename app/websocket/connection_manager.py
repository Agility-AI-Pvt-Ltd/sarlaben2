from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[tuple[UUID, UUID], set[WebSocket]] = defaultdict(
            set
        )

    async def connect(
        self, cattle_id: UUID, human_id: UUID, websocket: WebSocket
    ) -> None:
        await websocket.accept()
        self.active_connections[(cattle_id, human_id)].add(websocket)

    def disconnect(self, cattle_id: UUID, human_id: UUID, websocket: WebSocket) -> None:
        key = (cattle_id, human_id)
        self.active_connections[key].discard(websocket)
        if not self.active_connections[key]:
            self.active_connections.pop(key, None)

    async def send_json(self, cattle_id: UUID, human_id: UUID, payload: dict) -> None:
        for websocket in self.active_connections.get((cattle_id, human_id), set()):
            await websocket.send_json(payload)


connection_manager = ConnectionManager()
