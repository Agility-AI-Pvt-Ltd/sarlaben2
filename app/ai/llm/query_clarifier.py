from enum import StrEnum

from pydantic import BaseModel, ValidationError

from app.core.exceptions import ServiceUnavailableError


class QueryIntent(StrEnum):
    QUESTION = "question"
    AFFIRMATION = "affirmation"
    NEGATION = "negation"
    REQUEST_MORE = "request_more"
    PROVIDE_INFORMATION = "provide_information"
    GREETING = "greeting"
    UNCLEAR = "unclear"


class ResponseAction(StrEnum):
    ANSWER = "answer"
    ASK_CLARIFICATION = "ask_clarification"
    ASK_CATTLE_DETAILS = "ask_cattle_details"
    EMERGENCY_GUIDANCE = "emergency_guidance"


class QueryAnalysis(BaseModel):
    intent: QueryIntent
    normalized_request: str
    is_urgent: bool
    has_sufficient_cattle_information: bool
    missing_information: list[str]
    response_action: ResponseAction
    clarification_question: str | None
    response_strategy: str


class QueryAnalysisTool:
    name = "analyze_cattle_query"
    definition = {
        "type": "function",
        "name": name,
        "description": (
            "Analyze the farmer's latest message before an answer is written. "
            "Identify intent, urgency, missing cattle information, and the safest "
            "response action using the conversation and cattle history."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": [intent.value for intent in QueryIntent],
                    "description": "The farmer's primary conversational intent.",
                },
                "normalized_request": {
                    "type": "string",
                    "description": (
                        "A short standalone restatement of what the farmer means."
                    ),
                },
                "is_urgent": {
                    "type": "boolean",
                    "description": (
                        "Whether the reported situation needs immediate veterinary "
                        "escalation."
                    ),
                },
                "has_sufficient_cattle_information": {
                    "type": "boolean",
                    "description": (
                        "Whether the available facts are sufficient for a useful "
                        "and safe response."
                    ),
                },
                "missing_information": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Only the cattle details that are important for the next "
                        "response and are not already known."
                    ),
                },
                "response_action": {
                    "type": "string",
                    "enum": [action.value for action in ResponseAction],
                    "description": "The action the answer-writing call should take.",
                },
                "clarification_question": {
                    "type": ["string", "null"],
                    "description": (
                        "One concise question when the intent or a critical fact is "
                        "unclear, otherwise null."
                    ),
                },
                "response_strategy": {
                    "type": "string",
                    "description": (
                        "A concise decision summary for the answer-writing call. "
                        "Do not write the farmer-facing answer."
                    ),
                },
            },
            "required": [
                "intent",
                "normalized_request",
                "is_urgent",
                "has_sufficient_cattle_information",
                "missing_information",
                "response_action",
                "clarification_question",
                "response_strategy",
            ],
            "additionalProperties": False,
        },
    }

    async def analyze(
        self,
        *,
        client,
        model: str,
        latest_user_message: str,
        conversation_context: str,
        summarized_history: str,
        additional_context: str,
    ) -> QueryAnalysis:
        response = await client.responses.create(
            model=model,
            instructions=(
                "This is step 1: analyze only and do not answer the farmer. Resolve "
                "short replies from conversation context, inspect cattle history for "
                "missing facts, and identify urgent symptoms. Use emergency_guidance "
                "for severe injury, breathing difficulty, poisoning, inability to "
                "stand, or prolonged labor. Always call analyze_cattle_query exactly "
                "once with a concise response strategy, not hidden reasoning."
            ),
            input=(
                f"Recent conversation:\n{conversation_context}\n\n"
                f"Cattle history:\n{summarized_history}\n\n"
                f"Additional context:\n{additional_context}\n\n"
                f"Latest farmer message:\n{latest_user_message}"
            ),
            tools=[self.definition],
            tool_choice={"type": "function", "name": self.name},
            parallel_tool_calls=False,
        )

        for item in response.output:
            if item.type == "function_call" and item.name == self.name:
                try:
                    return QueryAnalysis.model_validate_json(item.arguments)
                except ValidationError as exc:
                    raise ServiceUnavailableError(
                        "The AI assistant returned an invalid query analysis"
                    ) from exc

        raise ServiceUnavailableError("The AI assistant did not analyze the query")
