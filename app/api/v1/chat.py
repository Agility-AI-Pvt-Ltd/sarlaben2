from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.chat import (
    AIMessageCreate,
    ChatMessageCreate,
    ChatMessageRead,
    ClearChatResponse,
    HumanAIMessageRead,
    ImageMessageCreate,
)
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
    "/cattle/{cattle_id}/human/{human_id}/with-ai-reply",
    response_model=HumanAIMessageRead,
    status_code=201,
)
async def create_human_message_with_ai_reply(
    cattle_id: UUID,
    human_id: UUID,
    payload: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
):
    return await ChatService(db).add_human_message_with_ai_reply(
        cattle_id, human_id, payload
    )


@router.post(
    "/cattle/{cattle_id}/human/{human_id}/image",
    response_model=ChatMessageRead,
    status_code=201,
)
async def create_image_message(
    cattle_id: UUID,
    human_id: UUID,
    payload: ImageMessageCreate,
    db: AsyncSession = Depends(get_db),
):
    return await ChatService(db).add_image_message(cattle_id, human_id, payload)


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


@router.delete(
    "/sessions/{session_id}/human/{human_id}",
    response_model=ClearChatResponse,
)
async def clear_session_messages(
    session_id: UUID,
    human_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await ChatService(db).clear_chat(session_id, human_id)
