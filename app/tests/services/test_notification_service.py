from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.schemas.notification import PushTokenCreate
from app.services import notification_service
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


@pytest.mark.asyncio
async def test_register_push_token_accepts_fcm_token() -> None:
    farmer_id = uuid4()
    created_token = object()
    payload = PushTokenCreate(
        farmer_id=farmer_id,
        expo_push_token="fcm_token_abcdefghijklmnopqrstuvwxyz1234567890",
        platform="android",
    )
    service = object.__new__(NotificationService)
    service.users = SimpleNamespace(get=AsyncMock(return_value=object()))
    service.push_tokens = SimpleNamespace(upsert=AsyncMock(return_value=created_token))

    result = await service.register_push_token(payload)

    assert result is created_token
    service.push_tokens.upsert.assert_awaited_once_with(payload)


@pytest.mark.asyncio
async def test_send_message_notification_sends_high_priority_expo_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    farmer_id = uuid4()
    cattle_id = uuid4()
    sent_requests: list[dict] = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> None:
            return None

        async def post(self, url: str, *, headers: dict, json: list[dict]):
            sent_requests.append({"headers": headers, "json": json, "url": url})
            return FakeResponse()

    monkeypatch.setattr(notification_service.httpx, "AsyncClient", FakeAsyncClient)

    service = object.__new__(NotificationService)
    service.push_tokens = SimpleNamespace(
        list_by_farmer=AsyncMock(
            return_value=[
                SimpleNamespace(expo_push_token="ExpoPushToken[abc12345678901234567890]")
            ]
        )
    )

    await service.send_message_notification(
        farmer_id=farmer_id,
        cattle_id=cattle_id,
        cattle_name="Lakshmi",
        message="Cow #15 is due tomorrow",
    )

    service.push_tokens.list_by_farmer.assert_awaited_once_with(farmer_id)
    assert sent_requests[0]["url"] == notification_service.EXPO_PUSH_SEND_URL
    payload = sent_requests[0]["json"][0]
    assert payload["to"] == "ExpoPushToken[abc12345678901234567890]"
    assert payload["title"] == "CowX AI: Lakshmi"
    assert payload["body"] == "Cow #15 is due tomorrow"
    assert payload["priority"] == "high"
    assert payload["sound"] == "default"
    assert payload["channelId"] == "cowx-messages"
    assert payload["data"] == {
        "type": "message",
        "cattleId": str(cattle_id),
        "url": f"/chat/{cattle_id}",
    }


@pytest.mark.asyncio
async def test_send_message_notification_sends_fcm_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    farmer_id = uuid4()
    cattle_id = uuid4()
    sent_batches = []

    class FakeBatchResponse:
        failure_count = 0
        success_count = 1

    def fake_send_each(messages):
        sent_batches.append(messages)
        return FakeBatchResponse()

    monkeypatch.setattr(notification_service.firebase_admin, "_apps", {"default": object()})
    monkeypatch.setattr(notification_service.messaging, "send_each", fake_send_each)

    service = object.__new__(NotificationService)
    service.push_tokens = SimpleNamespace(
        list_by_farmer=AsyncMock(
            return_value=[
                SimpleNamespace(
                    expo_push_token="fcm_token_abcdefghijklmnopqrstuvwxyz1234567890"
                )
            ]
        )
    )

    await service.send_message_notification(
        farmer_id=farmer_id,
        cattle_id=cattle_id,
        cattle_name="Lakshmi",
        message="Cow #15 is due tomorrow",
    )

    service.push_tokens.list_by_farmer.assert_awaited_once_with(farmer_id)
    message = sent_batches[0][0]
    assert message.token == "fcm_token_abcdefghijklmnopqrstuvwxyz1234567890"
    assert message.notification.title == "CowX AI: Lakshmi"
    assert message.notification.body == "Cow #15 is due tomorrow"
    assert message.data == {
        "type": "message",
        "cattleId": str(cattle_id),
        "url": f"/chat/{cattle_id}",
    }
    assert message.android.priority == "high"
    assert message.android.notification.channel_id == "cowx-messages"
    assert message.android.notification.sound == "default"
