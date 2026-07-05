from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.notification import PushTokenCreate, PushTokenRead
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/push-tokens", response_model=PushTokenRead, status_code=201)
async def register_push_token(
    payload: PushTokenCreate,
    db: AsyncSession = Depends(get_db),
):
    return await NotificationService(db).register_push_token(payload)
