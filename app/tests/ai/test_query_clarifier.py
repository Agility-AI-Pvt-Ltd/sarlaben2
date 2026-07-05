import json
from types import SimpleNamespace

import pytest

from app.ai.llm.query_clarifier import (
    QueryAnalysisTool,
    QueryIntent,
    ResponseAction,
)


class FakeResponses:
    def __init__(self) -> None:
        self.request = None

    async def create(self, **kwargs):
        self.request = kwargs
        arguments = json.dumps(
            {
                "intent": "affirmation",
                "normalized_request": (
                    "Yes, the farmer wants to continue the suggested monitoring."
                ),
                "is_urgent": False,
                "has_sufficient_cattle_information": True,
                "missing_information": [],
                "response_action": "answer",
                "clarification_question": None,
                "response_strategy": (
                    "Acknowledge the confirmation and continue monitoring guidance."
                ),
            }
        )
        return SimpleNamespace(
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="analyze_cattle_query",
                    arguments=arguments,
                )
            ]
        )


@pytest.mark.asyncio
async def test_query_analyzer_forces_strict_analysis_tool_call() -> None:
    responses = FakeResponses()
    client = SimpleNamespace(responses=responses)

    result = await QueryAnalysisTool().analyze(
        client=client,
        model="gpt-5.5",
        latest_user_message="Yes",
        cattle_profile="Name: Lakshmi\nTag number: TN-01",
        conversation_context=(
            "ai: Should you monitor her water intake for the next hour?\nhuman: Yes"
        ),
        summarized_history="health: Reduced water intake today.",
        additional_context="",
    )

    assert result.intent is QueryIntent.AFFIRMATION
    assert result.response_action is ResponseAction.ANSWER
    assert responses.request["tool_choice"] == {
        "type": "function",
        "name": "analyze_cattle_query",
    }
    assert responses.request["parallel_tool_calls"] is False
    assert "Name: Lakshmi" in responses.request["input"]
    assert "Tag number: TN-01" in responses.request["input"]
    assert "Reduced water intake today." in responses.request["input"]
    tool = responses.request["tools"][0]
    assert tool["strict"] is True
    assert tool["parameters"]["additionalProperties"] is False
