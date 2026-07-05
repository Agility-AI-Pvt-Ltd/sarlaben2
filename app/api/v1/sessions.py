from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.session import SessionCreate, SessionRead
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionRead, status_code=201)
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db)):
    return await SessionService(db).create_session(payload)


@router.get("/cattle/{cattle_id}/human/{human_id}", response_model=list[SessionRead])
async def list_sessions_for_cattle(
    cattle_id: UUID, human_id: UUID, db: AsyncSession = Depends(get_db)
):
    return await SessionService(db).list_for_cattle(cattle_id, human_id)


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    return await SessionService(db).get_session(session_id)
