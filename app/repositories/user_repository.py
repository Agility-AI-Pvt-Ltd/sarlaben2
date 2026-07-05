from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import utc_now
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, user_id: UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_phone(self, phone_number: str) -> User | None:
        stmt = select(User).where(User.phone_number == phone_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_verified(self, data: UserCreate) -> User:
        user = User(
            **data.model_dump(),
            is_phone_verified=True,
            phone_verified_at=utc_now(),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def mark_verified(self, user: User) -> User:
        user.is_phone_verified = True
        user.phone_verified_at = utc_now()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, data: UserUpdate) -> User:
        if data.full_name is not None:
            user.full_name = data.full_name
        if "profile_image_uri" in data.model_fields_set:
            user.profile_image_uri = data.profile_image_uri
        await self.db.commit()
        await self.db.refresh(user)
        return user
