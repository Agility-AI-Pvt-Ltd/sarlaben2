from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.user import (
    OTPRequest,
    OTPRequestResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/otp/send", response_model=OTPRequestResponse, status_code=202)
async def send_otp(
    payload: OTPRequest,
    db: AsyncSession = Depends(get_db),
) -> OTPRequestResponse:
    status = await AuthService(db).send_otp(payload)
    return OTPRequestResponse(phone_number=payload.phone_number, status=status)


@router.post("/otp/verify", response_model=OTPVerifyResponse)
async def verify_otp(
    payload: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> OTPVerifyResponse:
    user = await AuthService(db).verify_otp(payload)
    return OTPVerifyResponse(verified=True, user=user)
