from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.constants import CattleMemoryType
from app.core.exceptions import NotFoundError
from app.schemas.chat import AIMessageCreate, ImageMessageCreate
from app.services.chat_service import ChatService


@dataclass(frozen=True)
class FakeProfile:
    text: str
    name: str = "Lakshmi"

    def to_prompt(self) -> str:
        return self.text


@pytest.mark.asyncio
async def test_clear_chat_archives_messages_for_thirty_days() -> None:
    farmer_id = uuid4()
    session_id = uuid4()
    purge_after = datetime.now(timezone.utc)
    service = object.__new__(ChatService)
    service.session_repo = SimpleNamespace(
        get=AsyncMock(
            return_value=SimpleNamespace(
                farmer_id=farmer_id,
            )
        )
    )
    service.deleted_chat_repo = SimpleNamespace(
        archive_and_clear_session=AsyncMock(return_value=(7, purge_after)),
    )

    result = await service.clear_chat(session_id, farmer_id)

    assert result.archived_messages == 7
    assert result.purge_after is purge_after
    service.deleted_chat_repo.archive_and_clear_session.assert_awaited_once_with(
        session_id
    )


@pytest.mark.asyncio
async def test_clear_chat_rejects_another_farmer() -> None:
    service = object.__new__(ChatService)
    service.session_repo = SimpleNamespace(
        get=AsyncMock(
            return_value=SimpleNamespace(
                farmer_id=uuid4(),
            )
        )
    )
    service.deleted_chat_repo = SimpleNamespace(
        archive_and_clear_session=AsyncMock(),
    )

    with pytest.raises(NotFoundError):
        await service.clear_chat(uuid4(), uuid4())

    service.deleted_chat_repo.archive_and_clear_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_image_message_creates_image_without_ai_reply() -> None:
    cattle_id = uuid4()
    farmer_id = uuid4()
    session_id = uuid4()
    image_data_url = "data:image/jpeg;base64,aGVsbG8gd29ybGQ="
    created_message = object()

    service = object.__new__(ChatService)
    service._resolve_session_id = AsyncMock(return_value=session_id)
    service.chat_repo = SimpleNamespace(
        create_message=AsyncMock(return_value=created_message),
    )

    result = await service.add_image_message(
        cattle_id,
        farmer_id,
        ImageMessageCreate(
            session_id=session_id,
            image_data_url=image_data_url,
        ),
    )

    assert result is created_message
    service.chat_repo.create_message.assert_awaited_once_with(
        session_id=session_id,
        cattle_id=cattle_id,
        farmer_id=farmer_id,
        message=image_data_url,
        message_type="image",
    )


@pytest.mark.asyncio
async def test_add_ai_message_uses_ten_recent_messages_and_all_cattle_history() -> None:
    cattle_id = uuid4()
    farmer_id = uuid4()
    session_id = uuid4()
    created_message = SimpleNamespace(message="Keep monitoring.")

    service = object.__new__(ChatService)
    service._resolve_session_id = AsyncMock(return_value=session_id)
    service.chat_repo = SimpleNamespace(
        create_message=AsyncMock(return_value=created_message),
    )
    service.memory_repo = SimpleNamespace(
        create=AsyncMock(),
    )
    service.notification_service = SimpleNamespace(
        send_message_notification=AsyncMock(),
    )
    latest_human = SimpleNamespace(id=uuid4(), message_type="human", message="Older chat")
    cattle_context = SimpleNamespace(
        profile=FakeProfile("Name: Lakshmi\nTag number: TN-01"),
        latest_human_message=latest_human,
        conversation_context="human: Older chat\nai: Latest reply",
        summarized_history="health: Had a fever last week.\nmedicine: Received medicine today.",
    )
    service.cattle_context_tool = SimpleNamespace(
        load=AsyncMock(return_value=cattle_context)
    )
    service.llm = SimpleNamespace(
        generate_cattle_reply=AsyncMock(return_value="Keep monitoring."),
        extract_cattle_memories=AsyncMock(
            return_value=[
                SimpleNamespace(
                    cattle_data_text="Lakshmi had a fever last week.",
                    data_type_stored_by_ai=CattleMemoryType.MEDICAL,
                    confidence=0.9,
                )
            ]
        ),
    )

    result = await service.add_ai_message(
        cattle_id,
        farmer_id,
        AIMessageCreate(session_id=session_id),
    )

    assert result is created_message
    service.cattle_context_tool.load.assert_awaited_once_with(
        cattle_id=cattle_id,
        farmer_id=farmer_id,
        session_id=session_id,
    )
    service.llm.generate_cattle_reply.assert_awaited_once_with(
        cattle_id=cattle_id,
        farmer_id=farmer_id,
        cattle_profile="Name: Lakshmi\nTag number: TN-01",
        conversation_context="human: Older chat\nai: Latest reply",
        summarized_history=(
            "health: Had a fever last week.\nmedicine: Received medicine today."
        ),
        additional_context="",
        latest_user_message="Older chat",
    )
    service.llm.extract_cattle_memories.assert_awaited_once_with(
        cattle_profile="Name: Lakshmi\nTag number: TN-01",
        conversation_context="human: Older chat\nai: Latest reply",
        summarized_history=(
            "health: Had a fever last week.\nmedicine: Received medicine today."
        ),
        latest_user_message="Older chat",
        additional_context="",
    )
    saved_memory = service.memory_repo.create.await_args.args[1]
    assert saved_memory.cattle_data_text == "Lakshmi had a fever last week."
    assert saved_memory.data_type_stored_by_ai is CattleMemoryType.MEDICAL
    assert saved_memory.source_message_id == latest_human.id
    service.notification_service.send_message_notification.assert_awaited_once_with(
        farmer_id=farmer_id,
        cattle_id=cattle_id,
        cattle_name="Lakshmi",
        message="Keep monitoring.",
    )
