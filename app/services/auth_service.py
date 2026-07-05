from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidVerificationCodeError, NotFoundError
from app.repositories.user_repository import UserRepository
from app.schemas.user import OTPRequest, OTPVerifyRequest, UserCreate, UserUpdate
from app.services.twilio_verify_service import TwilioVerifyService


class AuthService:
    def __init__(
        self,
        db: AsyncSession,
        verifier: TwilioVerifyService | None = None,
    ) -> None:
        self.user_repo = UserRepository(db)
        self.verifier = verifier or TwilioVerifyService()

    async def send_otp(self, data: OTPRequest) -> tuple[str, bool]:
        user = await self.user_repo.get_by_phone(data.phone_number)
        status = await self.verifier.send_otp(data.phone_number)
        return status, user is not None

    async def verify_otp(self, data: OTPVerifyRequest):
        approved = await self.verifier.verify_otp(data.phone_number, data.code)
        if not approved:
            raise InvalidVerificationCodeError()

        user = await self.user_repo.get_by_phone(data.phone_number)
        if user is None:
            user_data = UserCreate(
                phone_number=data.phone_number,
                full_name=data.full_name,
                preferred_language=data.preferred_language,
            )
            return await self.user_repo.create_verified(user_data)
        return await self.user_repo.mark_verified(user)

    async def update_user(self, user_id: UUID, data: UserUpdate):
        user = await self.user_repo.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return await self.user_repo.update(user, data)
