from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.schemas.notification import PushTokenCreate
from app.services.notification_service import NotificationService


@pytest.mark.asyncio
async def test_register_push_token_requires_existing_farmer() -> None:
    farmer_id = uuid4()
    service = object.__new__(NotificationService)
    service.users = SimpleNamespace(get=AsyncMock(return_value=None))
    service.push_tokens = SimpleNamespace(upsert=AsyncMock())

    with pytest.raises(NotFoundError):
        await service.register_push_token(
            PushTokenCreate(
                farmer_id=farmer_id,
                expo_push_token="ExpoPushToken[abc12345678901234567890]",
                platform="android",
            )
        )

    service.push_tokens.upsert.assert_not_awaited()


@pytest.mark.asyncio
async def test_register_push_token_upserts_for_existing_farmer() -> None:
    farmer_id = uuid4()
    created_token = object()
    payload = PushTokenCreate(
        farmer_id=farmer_id,
        expo_push_token="ExpoPushToken[abc12345678901234567890]",
        platform="android",
    )
    service = object.__new__(NotificationService)
    service.users = SimpleNamespace(get=AsyncMock(return_value=object()))
    service.push_tokens = SimpleNamespace(upsert=AsyncMock(return_value=created_token))

    result = await service.register_push_token(payload)

    assert result is created_token
    service.push_tokens.upsert.assert_awaited_once_with(payload)
