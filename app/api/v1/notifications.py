from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.schemas.notification import (
    PushTokenCreate,
    PushTokenRead,
    TestNotificationRequest,
    TestNotificationResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/push-tokens", response_model=PushTokenRead, status_code=201)
async def register_push_token(
    payload: PushTokenCreate,
    db: AsyncSession = Depends(get_db),
):
    return await NotificationService(db).register_push_token(payload)


@router.post("/test", response_model=TestNotificationResponse)
async def send_test_notification(
    payload: TestNotificationRequest,
    db: AsyncSession = Depends(get_db),
    x_cowx_notification_test_key: str | None = Header(default=None),
):
    if (
        not settings.notification_test_key
        or x_cowx_notification_test_key != settings.notification_test_key
    ):
        raise NotFoundError("Notification test endpoint is not available")

    target = await NotificationService(db).send_test_notification(
        farmer_id=payload.farmer_id,
        token=payload.token,
        use_latest=payload.use_latest,
        title=payload.title,
        body=payload.body,
        cattle_id=payload.cattle_id,
        cattle_name=payload.cattle_name,
    )
    return TestNotificationResponse(sent=True, target=target)
