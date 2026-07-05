from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import ChatSession
from app.schemas.session import SessionCreate


class SessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: SessionCreate) -> ChatSession:
        session = ChatSession(**data.model_dump())
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get(self, session_id: UUID) -> ChatSession | None:
        return await self.db.get(ChatSession, session_id)

    async def list_for_cattle(
        self, cattle_id: UUID, farmer_id: UUID | None = None
    ) -> list[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.cattle_id == cattle_id)
            .order_by(ChatSession.created_at.desc())
        )
        if farmer_id:
            stmt = stmt.where(ChatSession.farmer_id == farmer_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
