import logging
from uuid import UUID

import openai
from openai import AsyncOpenAI

from app.ai.llm.prompt_builder import PromptBuilder
from app.ai.llm.query_clarifier import QueryAnalysisTool
from app.ai.llm.response_formatter import ResponseFormatter
from app.core.config import Settings, settings
from app.core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)


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
                conversation_context=conversation_context,
                summarized_history=summarized_history,
                additional_context=additional_context,
            )
            instructions = self.prompt_builder.build_cattle_health_instructions()
            prompt = self.prompt_builder.build_cattle_health_input(
                cattle_id=cattle_id,
                farmer_id=farmer_id,
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
