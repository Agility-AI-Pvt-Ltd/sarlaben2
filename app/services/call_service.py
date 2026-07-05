from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.call_repository import CallRepository
from app.schemas.call import CallLogCreate


class CallService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = CallRepository(db)

    async def create_call_log(self, data: CallLogCreate):
        return await self.repo.create(data)

    async def list_for_cattle(self, cattle_id: UUID):
        return await self.repo.list_for_cattle(cattle_id)

    async def list_for_farmer(self, farmer_id: UUID):
        return await self.repo.list_for_farmer(farmer_id)
