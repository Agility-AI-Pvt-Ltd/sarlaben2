from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.call import CallLogCreate, CallLogRead
from app.services.call_service import CallService

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("", response_model=CallLogRead, status_code=201)
async def create_call_log(payload: CallLogCreate, db: AsyncSession = Depends(get_db)):
    return await CallService(db).create_call_log(payload)


@router.get("/cattle/{cattle_id}", response_model=list[CallLogRead])
async def list_cattle_call_logs(cattle_id: UUID, db: AsyncSession = Depends(get_db)):
    return await CallService(db).list_for_cattle(cattle_id)
