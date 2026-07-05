from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.schemas.user import OTPVerifyRequest
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_verify_otp_creates_verified_user() -> None:
    created_user = object()
    service = object.__new__(AuthService)
    service.verifier = SimpleNamespace(verify_otp=AsyncMock(return_value=True))
    service.user_repo = SimpleNamespace(
        get_by_phone=AsyncMock(return_value=None),
        create_verified=AsyncMock(return_value=created_user),
    )
    payload = OTPVerifyRequest(
        phone_number="+919876543210",
        code="123456",
        full_name="Ravi",
        preferred_language="ta-IN",
    )

    result = await service.verify_otp(payload)

    assert result is created_user
    service.verifier.verify_otp.assert_awaited_once_with("+919876543210", "123456")
    created_data = service.user_repo.create_verified.await_args.args[0]
    assert created_data.phone_number == "+919876543210"
    assert created_data.full_name == "Ravi"
    assert created_data.preferred_language == "ta-IN"
