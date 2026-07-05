from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.chat_service import LLMChatService
from app.ai.memory.extractor import MemoryExtractor
from app.core.constants import CattleMemoryType, MessageType
from app.core.exceptions import NotFoundError
from app.repositories.chat_repository import ChatRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.chat import AIMessageCreate, CattleMemoryCreate, ChatMessageCreate
from app.schemas.session import SessionCreate


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self.chat_repo = ChatRepository(db)
        self.session_repo = SessionRepository(db)
        self.memory_repo = MemoryRepository(db)
        self.llm = LLMChatService()
        self.memory_extractor = MemoryExtractor()

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
        for memory in self.memory_extractor.extract(data.message):
            await self.memory_repo.create(
                cattle_id,
                CattleMemoryCreate(
                    cattle_data_text=memory.text,
                    data_type_stored_by_ai=CattleMemoryType(memory.memory_type),
                    source_message_id=message.id,
                    confidence=memory.confidence,
                ),
            )
        return message

    async def add_ai_message(
        self, cattle_id: UUID, farmer_id: UUID, data: AIMessageCreate
    ):
        session_id = await self._resolve_session_id(
            cattle_id, farmer_id, data.session_id
        )
        messages = await self.chat_repo.list_recent_messages(session_id, limit=10)
        memories = await self.memory_repo.list_for_cattle(cattle_id)
        conversation_context = "\n".join(
            f"{message.message_type}: {message.message}" for message in messages
        )
        latest_user_message = next(
            (
                message.message
                for message in reversed(messages)
                if message.message_type == MessageType.HUMAN.value
            ),
            data.context,
        )
        summarized_history = "\n".join(
            (f"{memory.data_type_stored_by_ai}: {memory.cattle_data_text}")
            for memory in reversed(memories)
        )
        text = await self.llm.generate_cattle_reply(
            cattle_id=cattle_id,
            farmer_id=farmer_id,
            conversation_context=conversation_context,
            summarized_history=summarized_history,
            additional_context=data.context,
            latest_user_message=latest_user_message,
        )
        return await self.chat_repo.create_message(
            session_id=session_id,
            cattle_id=cattle_id,
            farmer_id=farmer_id,
            message=text,
            message_type=MessageType.AI.value,
        )

    async def list_messages(self, session_id: UUID):
        return await self.chat_repo.list_messages(session_id)

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
