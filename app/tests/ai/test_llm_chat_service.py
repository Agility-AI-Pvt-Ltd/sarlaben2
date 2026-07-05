from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.ai.llm.chat_service import ExtractedCattleMemory, LLMChatService
from app.ai.llm.query_clarifier import (
    QueryAnalysis,
    QueryIntent,
    ResponseAction,
)
from app.core.config import Settings
from app.core.constants import CattleMemoryType
from app.core.exceptions import ServiceUnavailableError


class FakeResponses:
    def __init__(
        self,
        events: list[str],
        output_text: str = "  Monitor feed and water intake.  ",
    ) -> None:
        self.events = events
        self.output_text = output_text
        self.request: dict[str, str] | None = None

    async def create(self, **kwargs: str) -> SimpleNamespace:
        self.events.append("answer")
        self.request = kwargs
        return SimpleNamespace(output_text=self.output_text)


class FakeOpenAIClient:
    def __init__(self, responses: FakeResponses) -> None:
        self.responses = responses


@pytest.mark.asyncio
async def test_generate_cattle_reply_uses_responses_api() -> None:
    events: list[str] = []
    responses = FakeResponses(events)
    client = FakeOpenAIClient(responses)
    config = Settings(
        _env_file=None,
        OPENAI_API_KEY="test-key",
        OPENAI_MODEL="gpt-5.5",
    )
    analysis = QueryAnalysis(
        intent=QueryIntent.QUESTION,
        normalized_request="The cow is eating less today.",
        is_urgent=False,
        has_sufficient_cattle_information=True,
        missing_information=[],
        response_action=ResponseAction.ANSWER,
        clarification_question=None,
        response_strategy="Give concise monitoring guidance.",
    )

    async def analyze_query(**kwargs):
        events.append("analyze")
        return analysis

    query_analyzer = SimpleNamespace(analyze=AsyncMock(side_effect=analyze_query))
    service = LLMChatService(
        client=client,  # type: ignore[arg-type]
        config=config,
        query_analyzer=query_analyzer,  # type: ignore[arg-type]
    )
    cattle_id = uuid4()
    farmer_id = uuid4()

    result = await service.generate_cattle_reply(
        cattle_id=cattle_id,
        farmer_id=farmer_id,
        cattle_profile="Name: Lakshmi\nTag number: TN-01",
        conversation_context="human: The cow is eating less today.",
        summarized_history="health: Reduced appetite began yesterday.",
        additional_context="Temperature is normal.",
        latest_user_message="The cow is eating less today.",
    )

    assert result == "Monitor feed and water intake."
    assert responses.request is not None
    assert responses.request["model"] == "gpt-5.5"
    assert "The cow is eating less today." in responses.request["input"]
    assert "Reduced appetite began yesterday." in responses.request["input"]
    assert "Name: Lakshmi" in responses.request["input"]
    assert "Tag number: TN-01" in responses.request["input"]
    assert "Complete summarized cattle history:" in responses.request["input"]
    assert "Step 1 query analysis:" in responses.request["input"]
    assert "Intent: question" in responses.request["input"]
    assert "Response action: answer" in responses.request["input"]
    assert "contact a veterinarian immediately" in responses.request["instructions"]
    assert (
        "contains no useful facts about the animal" in responses.request["instructions"]
    )
    assert "Hindi written in Devanagari" in responses.request["instructions"]
    assert "Do not write full English sentences" in responses.request["instructions"]
    assert "doctor, vet, medicine, injection, feed, vaccine" in responses.request["instructions"]
    assert "Hindi language rule" in responses.request["input"]
    assert events == ["analyze", "answer"]
    query_analyzer.analyze.assert_awaited_once_with(
        client=client,
        model="gpt-5.5",
        latest_user_message="The cow is eating less today.",
        cattle_profile="Name: Lakshmi\nTag number: TN-01",
        conversation_context="human: The cow is eating less today.",
        summarized_history="health: Reduced appetite began yesterday.",
        additional_context="Temperature is normal.",
    )


@pytest.mark.asyncio
async def test_generate_cattle_reply_requires_api_key() -> None:
    config = Settings(_env_file=None, OPENAI_API_KEY=None)
    service = LLMChatService(config=config)

    with pytest.raises(ServiceUnavailableError, match="OPENAI_API_KEY"):
        await service.generate_cattle_reply(
            cattle_id=uuid4(),
            farmer_id=uuid4(),
            cattle_profile="Name: Lakshmi\nTag number: TN-01",
            conversation_context="human: Hello",
        )


@pytest.mark.asyncio
async def test_extract_cattle_memories_uses_strict_tool() -> None:
    class MemoryResponses:
        def __init__(self) -> None:
            self.request = None

        async def create(self, **kwargs):
            self.request = kwargs
            return SimpleNamespace(
                output=[
                    SimpleNamespace(
                        type="function_call",
                        name="save_cattle_memories",
                        arguments=(
                            '{"memories":[{"cattle_data_text":"Lakshmi has fever.",'
                            '"data_type_stored_by_ai":"medical","confidence":0.9}]}'
                        ),
                    )
                ]
            )

    responses = MemoryResponses()
    client = FakeOpenAIClient(responses)  # type: ignore[arg-type]
    service = LLMChatService(
        client=client,  # type: ignore[arg-type]
        config=Settings(_env_file=None, OPENAI_API_KEY="test-key"),
    )

    memories = await service.extract_cattle_memories(
        cattle_profile="Name: Lakshmi\nTag number: TN-01",
        conversation_context="human: Fever since morning",
        summarized_history="",
        latest_user_message="Fever since morning",
    )

    assert memories == [
        ExtractedCattleMemory(
            cattle_data_text="Lakshmi has fever.",
            data_type_stored_by_ai=CattleMemoryType.MEDICAL,
            confidence=0.9,
        )
    ]
    assert responses.request["tool_choice"] == {
        "type": "function",
        "name": "save_cattle_memories",
    }
    assert responses.request["tools"][0]["strict"] is True
    assert "Name: Lakshmi" in responses.request["input"]
    assert "Tag number: TN-01" in responses.request["input"]
