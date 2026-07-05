from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.chat import AIMessageCreate, ChatMessageCreate, ChatMessageRead
from app.services.chat_service import ChatService

router = APIRouter(prefix="/message", tags=["chat"])


@router.post(
    "/cattle/{cattle_id}/human/{human_id}",
    response_model=ChatMessageRead,
    status_code=201,
)
async def create_human_message(
    cattle_id: UUID,
    human_id: UUID,
    payload: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
):
    return await ChatService(db).add_human_message(cattle_id, human_id, payload)


@router.post(
    "/ai/human/{human_id}/cattle/{cattle_id}",
    response_model=ChatMessageRead,
    status_code=201,
)
async def create_ai_message(
    human_id: UUID,
    cattle_id: UUID,
    payload: AIMessageCreate,
    db: AsyncSession = Depends(get_db),
):
    return await ChatService(db).add_ai_message(cattle_id, human_id, payload)


@router.get("/sessions/{session_id}", response_model=list[ChatMessageRead])
async def list_session_messages(session_id: UUID, db: AsyncSession = Depends(get_db)):
    return await ChatService(db).list_messages(session_id)
