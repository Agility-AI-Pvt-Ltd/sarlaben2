from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import utc_now
from app.models.cattle_memory import CattleMemory
from app.models.chat_message import ChatMessage
from app.models.deleted_chat_message import DeletedChatMessage


class DeletedChatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def archive_and_clear_session(
        self,
        session_id: UUID,
    ) -> tuple[int, datetime | None]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .with_for_update()
        )
        messages = list(result.scalars().all())
        if not messages:
            return 0, None

        deleted_at = utc_now()
        purge_after = deleted_at + timedelta(days=30)
        message_ids = [message.id for message in messages]
        self.db.add_all(
            [
                DeletedChatMessage(
                    original_message_id=message.id,
                    session_id=message.session_id,
                    cattle_id=message.cattle_id,
                    farmer_id=message.farmer_id,
                    message=message.message,
                    message_type=message.message_type,
                    original_created_at=message.created_at,
                    original_updated_at=message.updated_at,
                    deleted_at=deleted_at,
                    purge_after=purge_after,
                )
                for message in messages
            ]
        )

        try:
            await self.db.execute(
                update(CattleMemory)
                .where(CattleMemory.source_message_id.in_(message_ids))
                .values(source_message_id=None)
            )
            await self.db.execute(
                delete(ChatMessage).where(ChatMessage.id.in_(message_ids))
            )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return len(messages), purge_after

    async def purge_expired(self) -> int:
        result = await self.db.execute(
            delete(DeletedChatMessage).where(
                DeletedChatMessage.purge_after <= utc_now()
            )
        )
        await self.db.commit()
        return result.rowcount or 0
