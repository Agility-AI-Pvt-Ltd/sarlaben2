from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.cattle import Cattle
from app.models.cattle_memory import CattleMemory
from app.models.chat_message import ChatMessage
from app.repositories.cattle_repository import CattleRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.memory_repository import MemoryRepository


@dataclass(frozen=True)
class CattleProfile:
    id: UUID
    farmer_id: UUID
    name: str
    cattle_tag: str
    breed: str | None
    sex: str | None
    date_of_birth: date | None
    notes: str | None

    @classmethod
    def from_model(cls, cattle: Cattle) -> "CattleProfile":
        return cls(
            id=cattle.id,
            farmer_id=cattle.farmer_id,
            name=cattle.name,
            cattle_tag=cattle.cattle_tag,
            breed=cattle.breed,
            sex=cattle.sex,
            date_of_birth=cattle.date_of_birth,
            notes=cattle.notes,
        )

    def to_prompt(self) -> str:
        facts = [
            f"Name: {self.name}",
            f"Tag number: {self.cattle_tag}",
            f"Cattle ID: {self.id}",
            f"Farmer ID: {self.farmer_id}",
        ]
        if self.breed:
            facts.append(f"Breed: {self.breed}")
        if self.sex:
            facts.append(f"Sex: {self.sex}")
        if self.date_of_birth:
            facts.append(f"Date of birth: {self.date_of_birth.isoformat()}")
        if self.notes:
            facts.append(f"Notes: {self.notes}")
        return "\n".join(facts)


@dataclass(frozen=True)
class CattleChatContext:
    profile: CattleProfile
    recent_messages: list[ChatMessage]
    memories: list[CattleMemory]

    @property
    def conversation_context(self) -> str:
        return "\n".join(
            f"{message.message_type}: {message.message}"
            for message in self.recent_messages
        )

    @property
    def summarized_history(self) -> str:
        return "\n".join(
            f"{memory.data_type_stored_by_ai}: {memory.cattle_data_text}"
            for memory in reversed(self.memories)
        )

    @property
    def latest_human_message(self) -> ChatMessage | None:
        return next(
            (
                message
                for message in reversed(self.recent_messages)
                if message.message_type == "human"
            ),
            None,
        )


class CattleContextTool:
    """Loads the DB facts the LLM needs before answering a cattle chat."""

    def __init__(self, db: AsyncSession) -> None:
        self.cattle_repo = CattleRepository(db)
        self.chat_repo = ChatRepository(db)
        self.memory_repo = MemoryRepository(db)

    async def load(
        self,
        *,
        cattle_id: UUID,
        farmer_id: UUID,
        session_id: UUID,
        recent_message_limit: int = 10,
    ) -> CattleChatContext:
        cattle = await self.cattle_repo.get(cattle_id)
        if not cattle or cattle.farmer_id != farmer_id:
            raise NotFoundError("Cattle not found")

        recent_messages = await self.chat_repo.list_recent_messages(
            session_id, limit=recent_message_limit
        )
        memories = await self.memory_repo.list_for_cattle(cattle_id)
        return CattleChatContext(
            profile=CattleProfile.from_model(cattle),
            recent_messages=recent_messages,
            memories=memories,
        )
