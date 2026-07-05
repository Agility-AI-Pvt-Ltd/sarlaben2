from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage


class ChatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_message(
        self,
        *,
        session_id: UUID,
        cattle_id: UUID,
        farmer_id: UUID,
        message: str,
        message_type: str,
    ) -> ChatMessage:
        chat_message = ChatMessage(
            session_id=session_id,
            cattle_id=cattle_id,
            farmer_id=farmer_id,
            message=message,
            message_type=message_type,
        )
        self.db.add(chat_message)
        await self.db.commit()
        await self.db.refresh(chat_message)
        return chat_message

    async def list_messages(self, session_id: UUID) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_recent_messages(
        self, session_id: UUID, limit: int = 10
    ) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(reversed(result.scalars().all()))
