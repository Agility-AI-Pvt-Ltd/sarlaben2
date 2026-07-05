from uuid import UUID
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.cattle_repository import CattleRepository
from app.repositories.memory_repository import MemoryRepository
from app.schemas.cattle import CattleCreate, CattleUpdate
from app.schemas.chat import CattleMemoryCreate


class CattleService:
    def __init__(self, db: AsyncSession) -> None:
        self.cattle_repo = CattleRepository(db)
        self.memory_repo = MemoryRepository(db)

    async def create_cattle(self, data: CattleCreate):
        if data.cattle_tag is None:
            data = data.model_copy(
                update={"cattle_tag": await self._generate_unique_cattle_tag()}
            )
        return await self.cattle_repo.create(data)

    async def _generate_unique_cattle_tag(self) -> str:
        while True:
            cattle_tag = f"COW-{uuid4().hex.upper()}"
            if await self.cattle_repo.get_by_tag(cattle_tag) is None:
                return cattle_tag

    async def get_cattle(self, cattle_id: UUID):
        cattle = await self.cattle_repo.get(cattle_id)
        if not cattle:
            raise NotFoundError("Cattle not found")
        return cattle

    async def list_cattle(self, farmer_id: UUID | None = None):
        return await self.cattle_repo.list_by_farmer(farmer_id)

    async def update_cattle(self, cattle_id: UUID, data: CattleUpdate):
        cattle = await self.get_cattle(cattle_id)
        return await self.cattle_repo.update(cattle, data)

    async def delete_cattle(self, cattle_id: UUID) -> None:
        cattle = await self.get_cattle(cattle_id)
        await self.cattle_repo.delete(cattle)

    async def add_memory(self, cattle_id: UUID, data: CattleMemoryCreate):
        await self.get_cattle(cattle_id)
        return await self.memory_repo.create(cattle_id, data)

    async def list_memories(self, cattle_id: UUID):
        await self.get_cattle(cattle_id)
        return await self.memory_repo.list_for_cattle(cattle_id)
