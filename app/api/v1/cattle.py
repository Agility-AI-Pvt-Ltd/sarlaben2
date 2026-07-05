from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.cattle import CattleCreate, CattleRead, CattleUpdate
from app.schemas.chat import CattleMemoryCreate, CattleMemoryRead
from app.services.cattle_service import CattleService

router = APIRouter(prefix="/cattle", tags=["cattle"])


@router.post("", response_model=CattleRead, status_code=201)
async def create_cattle(payload: CattleCreate, db: AsyncSession = Depends(get_db)):
    return await CattleService(db).create_cattle(payload)


@router.get("", response_model=list[CattleRead])
async def list_cattle(
    farmer_id: UUID | None = None, db: AsyncSession = Depends(get_db)
):
    return await CattleService(db).list_cattle(farmer_id)


@router.get("/{cattle_id}", response_model=CattleRead)
async def get_cattle(cattle_id: UUID, db: AsyncSession = Depends(get_db)):
    return await CattleService(db).get_cattle(cattle_id)


@router.patch("/{cattle_id}", response_model=CattleRead)
async def update_cattle(
    cattle_id: UUID, payload: CattleUpdate, db: AsyncSession = Depends(get_db)
):
    return await CattleService(db).update_cattle(cattle_id, payload)


@router.post("/{cattle_id}/memories", response_model=CattleMemoryRead, status_code=201)
async def add_cattle_memory(
    cattle_id: UUID, payload: CattleMemoryCreate, db: AsyncSession = Depends(get_db)
):
    return await CattleService(db).add_memory(cattle_id, payload)


@router.get("/{cattle_id}/memories", response_model=list[CattleMemoryRead])
async def list_cattle_memories(cattle_id: UUID, db: AsyncSession = Depends(get_db)):
    return await CattleService(db).list_memories(cattle_id)
