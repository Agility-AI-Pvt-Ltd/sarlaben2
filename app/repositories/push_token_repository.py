from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import utc_now
from app.models.push_token import PushToken
from app.schemas.notification import PushTokenCreate


class PushTokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upsert(self, data: PushTokenCreate) -> PushToken:
        stmt = select(PushToken).where(
            PushToken.expo_push_token == data.expo_push_token
        )
        result = await self.db.execute(stmt)
        token = result.scalar_one_or_none()

        if token:
            token.farmer_id = data.farmer_id
            token.platform = data.platform
            token.device_id = data.device_id
            token.last_seen_at = utc_now()
        else:
            token = PushToken(
                farmer_id=data.farmer_id,
                expo_push_token=data.expo_push_token,
                platform=data.platform,
                device_id=data.device_id,
                last_seen_at=utc_now(),
            )
            self.db.add(token)

        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def list_by_farmer(self, farmer_id: UUID) -> list[PushToken]:
        stmt = select(PushToken).where(PushToken.farmer_id == farmer_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
