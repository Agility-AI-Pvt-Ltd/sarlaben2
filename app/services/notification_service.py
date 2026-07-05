import logging
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.push_token_repository import PushTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.notification import PushTokenCreate


logger = logging.getLogger(__name__)

EXPO_PUSH_SEND_URL = "https://exp.host/--/api/v2/push/send"


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

        payloads = [
            {
                "to": token.expo_push_token,
                "sound": "default",
                "title": f"CowX AI: {cattle_name}",
                "body": preview,
                "data": {
                    "type": "message",
                    "cattleId": str(cattle_id),
                    "url": f"/chat/{cattle_id}",
                },
                "channelId": "cowx-messages",
            }
            for token in tokens
        ]

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

        logger.info(
            "Sent message push notification",
            extra={"farmer_id": str(farmer_id), "token_count": len(tokens)},
        )
