from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.schemas.user import OTPVerifyRequest, UserUpdate
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


@pytest.mark.asyncio
async def test_update_user_updates_existing_user() -> None:
    user_id = uuid4()
    existing_user = object()
    updated_user = object()
    service = object.__new__(AuthService)
    service.user_repo = SimpleNamespace(
        get=AsyncMock(return_value=existing_user),
        update=AsyncMock(return_value=updated_user),
    )
    payload = UserUpdate(
        full_name="  Ravi Kumar  ",
        profile_image_uri="  file:///tmp/profile.jpg  ",
    )

    result = await service.update_user(user_id, payload)

    assert result is updated_user
    service.user_repo.get.assert_awaited_once_with(user_id)
    service.user_repo.update.assert_awaited_once_with(existing_user, payload)
    assert payload.full_name == "Ravi Kumar"
    assert payload.profile_image_uri == "file:///tmp/profile.jpg"


@pytest.mark.asyncio
async def test_update_user_raises_for_missing_user() -> None:
    service = object.__new__(AuthService)
    service.user_repo = SimpleNamespace(get=AsyncMock(return_value=None))

    with pytest.raises(NotFoundError):
        await service.update_user(uuid4(), UserUpdate(full_name="Ravi"))
