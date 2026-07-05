from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.constants import CattleMemoryType
from app.schemas.chat import AIMessageCreate
from app.services.chat_service import ChatService


@dataclass(frozen=True)
class FakeProfile:
    text: str
    name: str = "Lakshmi"

    def to_prompt(self) -> str:
        return self.text


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
