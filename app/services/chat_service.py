import asyncio
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.chat_service import LLMChatService
from app.core.constants import MessageType
from app.core.exceptions import NotFoundError
from app.repositories.chat_repository import ChatRepository
from app.repositories.deleted_chat_repository import DeletedChatRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.chat import (
    AIMessageCreate,
    CattleMemoryCreate,
    ChatMessageCreate,
    ClearChatResponse,
    ImageMessageCreate,
)
from app.schemas.session import SessionCreate
from app.services.cattle_context_tool import CattleContextTool
from app.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self.chat_repo = ChatRepository(db)
        self.deleted_chat_repo = DeletedChatRepository(db)
        self.session_repo = SessionRepository(db)
        self.memory_repo = MemoryRepository(db)
        self.cattle_context_tool = CattleContextTool(db)
        self.notification_service = NotificationService(db)
        self.llm = LLMChatService()

    async def add_human_message(
        self, cattle_id: UUID, farmer_id: UUID, data: ChatMessageCreate
    ):
        session_id = await self._resolve_session_id(
            cattle_id, farmer_id, data.session_id
        )
        message = await self.chat_repo.create_message(
            session_id=session_id,
            cattle_id=cattle_id,
            farmer_id=farmer_id,
            message=data.message,
            message_type=MessageType.HUMAN.value,
        )
        return message

    async def add_human_message_with_ai_reply(
        self, cattle_id: UUID, farmer_id: UUID, data: ChatMessageCreate
    ):
        human_message = await self.add_human_message(cattle_id, farmer_id, data)
        ai_message = await self.add_ai_message(
            cattle_id,
            farmer_id,
            AIMessageCreate(session_id=human_message.session_id),
        )
        return {
            "human_message": human_message,
            "ai_message": ai_message,
        }

    async def add_image_message(
        self, cattle_id: UUID, farmer_id: UUID, data: ImageMessageCreate
    ):
        session_id = await self._resolve_session_id(
            cattle_id, farmer_id, data.session_id
        )
        return await self.chat_repo.create_message(
            session_id=session_id,
            cattle_id=cattle_id,
            farmer_id=farmer_id,
            message=data.image_data_url,
            message_type=MessageType.IMAGE.value,
        )

    async def add_ai_message(
        self, cattle_id: UUID, farmer_id: UUID, data: AIMessageCreate
    ):
        session_id = await self._resolve_session_id(
            cattle_id, farmer_id, data.session_id
        )
        cattle_context = await self.cattle_context_tool.load(
            cattle_id=cattle_id,
            farmer_id=farmer_id,
            session_id=session_id,
        )
        latest_human_message = cattle_context.latest_human_message
        latest_user_message = (
            latest_human_message.message if latest_human_message else data.context
        )
        cattle_profile = cattle_context.profile.to_prompt()

        reply_task = self.llm.generate_cattle_reply(
            cattle_id=cattle_id,
            farmer_id=farmer_id,
            cattle_profile=cattle_profile,
            conversation_context=cattle_context.conversation_context,
            summarized_history=cattle_context.summarized_history,
            additional_context=data.context,
            latest_user_message=latest_user_message,
        )
        memory_task = self.llm.extract_cattle_memories(
            cattle_profile=cattle_profile,
            conversation_context=cattle_context.conversation_context,
            summarized_history=cattle_context.summarized_history,
            latest_user_message=latest_user_message,
            additional_context=data.context,
        )
        text_result, memory_result = await asyncio.gather(
            reply_task, memory_task, return_exceptions=True
        )
        if isinstance(text_result, Exception):
            raise text_result
        if isinstance(memory_result, Exception):
            logger.error(
                "Cattle memory extraction failed",
                exc_info=(
                    type(memory_result),
                    memory_result,
                    memory_result.__traceback__,
                ),
            )
            extracted_memories = []
        else:
            extracted_memories = memory_result

        ai_message = await self.chat_repo.create_message(
            session_id=session_id,
            cattle_id=cattle_id,
            farmer_id=farmer_id,
            message=text_result,
            message_type=MessageType.AI.value,
        )
        for memory in extracted_memories:
            await self.memory_repo.create(
                cattle_id,
                CattleMemoryCreate(
                    cattle_data_text=memory.cattle_data_text,
                    data_type_stored_by_ai=memory.data_type_stored_by_ai,
                    source_message_id=latest_human_message.id
                    if latest_human_message
                    else None,
                    confidence=memory.confidence,
                ),
            )
        try:
            await self.notification_service.send_message_notification(
                farmer_id=farmer_id,
                cattle_id=cattle_id,
                cattle_name=cattle_context.profile.name,
                message=ai_message.message,
            )
        except Exception:
            logger.warning("Failed to send message push notification", exc_info=True)
        return ai_message

    async def list_messages(self, session_id: UUID):
        return await self.chat_repo.list_messages(session_id)

    async def clear_chat(self, session_id: UUID, farmer_id: UUID) -> ClearChatResponse:
        session = await self.session_repo.get(session_id)
        if not session or session.farmer_id != farmer_id:
            raise NotFoundError("Session not found")

        archived_messages, purge_after = (
            await self.deleted_chat_repo.archive_and_clear_session(session_id)
        )
        return ClearChatResponse(
            archived_messages=archived_messages,
            purge_after=purge_after,
        )

    async def _resolve_session_id(
        self, cattle_id: UUID, farmer_id: UUID, session_id: UUID | None
    ) -> UUID:
        if session_id:
            session = await self.session_repo.get(session_id)
            if (
                not session
                or session.cattle_id != cattle_id
                or session.farmer_id != farmer_id
            ):
                raise NotFoundError("Session not found")
            return session.id
        session = await self.session_repo.create(
            SessionCreate(cattle_id=cattle_id, farmer_id=farmer_id)
        )
        return session.id
