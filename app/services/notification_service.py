import asyncio
import logging
from uuid import UUID

import firebase_admin
import httpx
from firebase_admin import messaging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.push_token_repository import PushTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.notification import PushTokenCreate


logger = logging.getLogger(__name__)

EXPO_PUSH_SEND_URL = "https://exp.host/--/api/v2/push/send"


def is_expo_push_token(token: str) -> bool:
    return token.startswith(("ExpoPushToken[", "ExponentPushToken["))


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.push_tokens = PushTokenRepository(db)
        self.users = UserRepository(db)

    async def register_push_token(self, data: PushTokenCreate):
        user = await self.users.get(data.farmer_id)
        if not user:
            raise NotFoundError("Farmer not found")
        return await self.push_tokens.upsert(data)

    async def send_message_notification(
        self,
        *,
        farmer_id: UUID,
        cattle_id: UUID,
        cattle_name: str,
        message: str,
    ) -> None:
        tokens = await self.push_tokens.list_by_farmer(farmer_id)
        if not tokens:
            return

        preview = " ".join(message.split())
        if len(preview) > 140:
            preview = f"{preview[:137]}..."

        title = f"CowX AI: {cattle_name}"
        data = {
            "type": "message",
            "cattleId": str(cattle_id),
            "url": f"/chat/{cattle_id}",
        }
        expo_payloads = []
        fcm_messages = []
        for token in tokens:
            if is_expo_push_token(token.expo_push_token):
                expo_payloads.append(
                    {
                        "to": token.expo_push_token,
                        "sound": "default",
                        "title": title,
                        "body": preview,
                        "priority": "high",
                        "data": data,
                        "channelId": "cowx-messages",
                    }
                )
            else:
                fcm_messages.append(
                    messaging.Message(
                        token=token.expo_push_token,
                        notification=messaging.Notification(
                            title=title,
                            body=preview,
                        ),
                        data=data,
                        android=messaging.AndroidConfig(
                            priority="high",
                            notification=messaging.AndroidNotification(
                                channel_id="cowx-messages",
                                sound="default",
                            ),
                        ),
                    )
                )

        if expo_payloads:
            await self._send_expo_notifications(expo_payloads)

        if fcm_messages:
            await self._send_fcm_notifications(fcm_messages)

        logger.info(
            "Sent message push notification",
            extra={"farmer_id": str(farmer_id), "token_count": len(tokens)},
        )

    async def _send_expo_notifications(self, payloads: list[dict]) -> None:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                EXPO_PUSH_SEND_URL,
                headers={
                    "Accept": "application/json",
                    "Accept-encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                },
                json=payloads,
            )
            response.raise_for_status()

    async def _send_fcm_notifications(
        self, messages: list[messaging.Message]
    ) -> None:
        if not firebase_admin._apps:
            logger.warning("Firebase Admin SDK is not configured; skipping FCM push")
            return

        response = await asyncio.to_thread(messaging.send_each, messages)
        if response.failure_count:
            logger.warning(
                "Some FCM push notifications failed",
                extra={
                    "failure_count": response.failure_count,
                    "success_count": response.success_count,
                },
            )
