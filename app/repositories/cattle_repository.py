from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cattle import Cattle
from app.schemas.cattle import CattleCreate, CattleUpdate


class CattleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: CattleCreate) -> Cattle:
        cattle = Cattle(**data.model_dump())
        self.db.add(cattle)
        await self.db.commit()
        await self.db.refresh(cattle)
        return cattle

    async def get(self, cattle_id: UUID) -> Cattle | None:
        return await self.db.get(Cattle, cattle_id)

    async def get_by_tag(self, cattle_tag: str) -> Cattle | None:
        result = await self.db.execute(
            select(Cattle).where(Cattle.cattle_tag == cattle_tag)
        )
        return result.scalar_one_or_none()

    async def list_by_farmer(self, farmer_id: UUID | None = None) -> list[Cattle]:
        stmt = select(Cattle).order_by(Cattle.created_at.desc())
        if farmer_id:
            stmt = stmt.where(Cattle.farmer_id == farmer_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, cattle: Cattle, data: CattleUpdate) -> Cattle:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(cattle, key, value)
        await self.db.commit()
        await self.db.refresh(cattle)
        return cattle
