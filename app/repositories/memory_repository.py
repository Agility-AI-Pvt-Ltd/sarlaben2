from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cattle_memory import CattleMemory
from app.schemas.chat import CattleMemoryCreate


class MemoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, cattle_id: UUID, data: CattleMemoryCreate) -> CattleMemory:
        memory = CattleMemory(cattle_id=cattle_id, **data.model_dump(mode="json"))
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def list_for_cattle(self, cattle_id: UUID) -> list[CattleMemory]:
        stmt = (
            select(CattleMemory)
            .where(CattleMemory.cattle_id == cattle_id)
            .order_by(CattleMemory.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
