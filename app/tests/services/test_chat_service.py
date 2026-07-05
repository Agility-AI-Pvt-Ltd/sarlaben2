from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.schemas.chat import AIMessageCreate
from app.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_add_ai_message_uses_ten_recent_messages_and_all_cattle_history() -> None:
    cattle_id = uuid4()
    farmer_id = uuid4()
    session_id = uuid4()
    created_message = object()

    service = object.__new__(ChatService)
    service._resolve_session_id = AsyncMock(return_value=session_id)
    service.chat_repo = SimpleNamespace(
        list_recent_messages=AsyncMock(
            return_value=[
                SimpleNamespace(message_type="human", message="Older chat"),
                SimpleNamespace(message_type="ai", message="Latest reply"),
            ]
        ),
        create_message=AsyncMock(return_value=created_message),
    )
    service.memory_repo = SimpleNamespace(
        list_for_cattle=AsyncMock(
            return_value=[
                SimpleNamespace(
                    data_type_stored_by_ai="medicine",
                    cattle_data_text="Received medicine today.",
                ),
                SimpleNamespace(
                    data_type_stored_by_ai="health",
                    cattle_data_text="Had a fever last week.",
                ),
            ]
        )
    )
    service.llm = SimpleNamespace(
        generate_cattle_reply=AsyncMock(return_value="Keep monitoring.")
    )

    result = await service.add_ai_message(
        cattle_id,
        farmer_id,
        AIMessageCreate(session_id=session_id),
    )

    assert result is created_message
    service.chat_repo.list_recent_messages.assert_awaited_once_with(
        session_id, limit=10
    )
    service.memory_repo.list_for_cattle.assert_awaited_once_with(cattle_id)
    service.llm.generate_cattle_reply.assert_awaited_once_with(
        cattle_id=cattle_id,
        farmer_id=farmer_id,
        conversation_context="human: Older chat\nai: Latest reply",
        summarized_history=(
            "health: Had a fever last week.\nmedicine: Received medicine today."
        ),
        additional_context="",
        latest_user_message="Older chat",
    )
