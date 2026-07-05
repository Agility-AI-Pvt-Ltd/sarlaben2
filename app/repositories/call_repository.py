from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call_log import CallLog
from app.schemas.call import CallLogCreate


class CallRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: CallLogCreate) -> CallLog:
        call_log = CallLog(**data.model_dump())
        self.db.add(call_log)
        await self.db.commit()
        await self.db.refresh(call_log)
        return call_log

    async def list_for_cattle(self, cattle_id: UUID) -> list[CallLog]:
        stmt = (
            select(CallLog)
            .where(CallLog.cattle_id == cattle_id)
            .order_by(CallLog.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_for_farmer(self, farmer_id: UUID) -> list[CallLog]:
        stmt = (
            select(CallLog)
            .where(CallLog.farmer_id == farmer_id)
            .order_by(CallLog.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
