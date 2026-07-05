from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.session_repository import SessionRepository
from app.schemas.session import SessionCreate


class SessionService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = SessionRepository(db)

    async def create_session(self, data: SessionCreate):
        return await self.repo.create(data)

    async def get_session(self, session_id: UUID):
        session = await self.repo.get(session_id)
        if not session:
            raise NotFoundError("Session not found")
        return session

    async def list_for_cattle(self, cattle_id: UUID, farmer_id: UUID | None = None):
        return await self.repo.list_for_cattle(cattle_id, farmer_id)
