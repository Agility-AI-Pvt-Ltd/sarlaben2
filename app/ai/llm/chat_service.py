import logging
from uuid import UUID

import openai
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from app.core.constants import CattleMemoryType
from app.ai.llm.prompt_builder import PromptBuilder
from app.ai.llm.query_clarifier import QueryAnalysisTool
from app.ai.llm.response_formatter import ResponseFormatter
from app.core.config import Settings, settings
from app.core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)


class ExtractedCattleMemory(BaseModel):
    cattle_data_text: str = Field(min_length=1)
    data_type_stored_by_ai: CattleMemoryType
    confidence: float = Field(ge=0, le=1)


class ExtractedCattleMemories(BaseModel):
    memories: list[ExtractedCattleMemory]


class LLMChatService:
    def __init__(
        self,
        client: AsyncOpenAI | None = None,
        config: Settings = settings,
        query_analyzer: QueryAnalysisTool | None = None,
    ) -> None:
        self.config = config
        self.client = client
        self.prompt_builder = PromptBuilder()
        self.query_analyzer = query_analyzer or QueryAnalysisTool()
        self.formatter = ResponseFormatter()

    async def generate_cattle_reply(
        self,
        cattle_id: UUID,
        farmer_id: UUID,
        cattle_profile: str,
        conversation_context: str,
        summarized_history: str = "",
        additional_context: str = "",
        latest_user_message: str = "",
    ) -> str:
        client = self._get_client()

        try:
            query_analysis = await self.query_analyzer.analyze(
                client=client,
                model=self.config.openai_model,
                latest_user_message=latest_user_message,
                cattle_profile=cattle_profile,
                conversation_context=conversation_context,
                summarized_history=summarized_history,
                additional_context=additional_context,
            )
            instructions = self.prompt_builder.build_cattle_health_instructions()
            prompt = self.prompt_builder.build_cattle_health_input(
                cattle_id=cattle_id,
                farmer_id=farmer_id,
                cattle_profile=cattle_profile,
                conversation_context=conversation_context,
                summarized_history=summarized_history,
                additional_context=additional_context,
                query_analysis=query_analysis,
            )
            response = await client.responses.create(
                model=self.config.openai_model,
                instructions=instructions,
                input=prompt,
            )
        except openai.APIError as exc:
            logger.exception("OpenAI request failed")
            raise ServiceUnavailableError(
                "The AI assistant is temporarily unavailable"
            ) from exc

        text = self.formatter.format_text(response.output_text)
        if not text:
            raise ServiceUnavailableError("The AI assistant returned an empty response")
        return text

    async def extract_cattle_memories(
        self,
        *,
        cattle_profile: str,
        conversation_context: str,
        summarized_history: str,
        latest_user_message: str,
        additional_context: str = "",
    ) -> list[ExtractedCattleMemory]:
        if not latest_user_message.strip():
            return []

        client = self._get_client()
        tool_name = "save_cattle_memories"
        tool = {
            "type": "function",
            "name": tool_name,
            "description": "Return structured durable cattle facts to save in the DB.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "memories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "cattle_data_text": {
                                    "type": "string",
                                    "description": (
                                        "One concise durable fact from the farmer."
                                    ),
                                },
                                "data_type_stored_by_ai": {
                                    "type": "string",
                                    "enum": [
                                        memory_type.value
                                        for memory_type in CattleMemoryType
                                    ],
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                            },
                            "required": [
                                "cattle_data_text",
                                "data_type_stored_by_ai",
                                "confidence",
                            ],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["memories"],
                "additionalProperties": False,
            },
        }

        try:
            response = await client.responses.create(
                model=self.config.openai_model,
                instructions=self.prompt_builder.build_memory_extraction_instructions(),
                input=self.prompt_builder.build_memory_extraction_input(
                    cattle_profile=cattle_profile,
                    conversation_context=conversation_context,
                    summarized_history=summarized_history,
                    latest_user_message=latest_user_message,
                    additional_context=additional_context,
                ),
                tools=[tool],
                tool_choice={"type": "function", "name": tool_name},
                parallel_tool_calls=False,
            )
        except openai.APIError as exc:
            logger.exception("OpenAI memory extraction request failed")
            raise ServiceUnavailableError(
                "The AI assistant could not save cattle details"
            ) from exc

        for item in response.output:
            if item.type == "function_call" and item.name == tool_name:
                try:
                    return ExtractedCattleMemories.model_validate_json(
                        item.arguments
                    ).memories
                except ValidationError as exc:
                    raise ServiceUnavailableError(
                        "The AI assistant returned invalid cattle details"
                    ) from exc

        raise ServiceUnavailableError("The AI assistant did not return cattle details")

    def _get_client(self) -> AsyncOpenAI:
        if self.client is not None:
            return self.client
        if not self.config.openai_api_key:
            raise ServiceUnavailableError("OPENAI_API_KEY is not configured")

        self.client = AsyncOpenAI(
            api_key=self.config.openai_api_key,
            timeout=self.config.openai_timeout_seconds,
            max_retries=self.config.openai_max_retries,
        )
        return self.client
