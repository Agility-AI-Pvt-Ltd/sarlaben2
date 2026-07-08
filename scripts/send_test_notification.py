import argparse
import asyncio
from uuid import UUID, uuid4

import firebase_admin
import httpx
from firebase_admin import messaging
from sqlalchemy import select

from app.core.firebase import initialize_firebase_admin
from app.database.session import SessionLocal
from app.models.push_token import PushToken
from app.services.notification_service import (
    EXPO_PUSH_SEND_URL,
    NotificationService,
    is_expo_push_token,
)


def token_label(token: str) -> str:
    return f"{token[:24]}..." if len(token) > 24 else token


async def send_raw_token(token: str, title: str, body: str, cattle_id: str) -> None:
    data = {
        "type": "message",
        "cattleId": cattle_id,
        "url": f"/chat/{cattle_id}",
    }

    if is_expo_push_token(token):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                EXPO_PUSH_SEND_URL,
                headers={
                    "Accept": "application/json",
                    "Accept-encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                },
                json=[
                    {
                        "to": token,
                        "sound": "default",
                        "title": title,
                        "body": body,
                        "priority": "high",
                        "data": data,
                        "channelId": "cowx-messages",
                    }
                ],
            )
            response.raise_for_status()
            print(response.text)
        return

    initialize_firebase_admin()
    if not firebase_admin._apps:
        raise RuntimeError("Firebase Admin SDK is not configured.")

    message = messaging.Message(
        token=token,
        notification=messaging.Notification(title=title, body=body),
        data=data,
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                channel_id="cowx-messages",
                sound="default",
            ),
        ),
    )
    message_id = await asyncio.to_thread(messaging.send, message)
    print(f"FCM message id: {message_id}")


async def latest_token() -> str | None:
    async with SessionLocal() as db:
        result = await db.execute(
            select(PushToken).order_by(PushToken.last_seen_at.desc()).limit(1)
        )
        token = result.scalar_one_or_none()
        return token.expo_push_token if token else None


async def send_to_farmer(
    farmer_id: UUID,
    body: str,
    cattle_id: UUID,
    cattle_name: str,
) -> None:
    async with SessionLocal() as db:
        service = NotificationService(db)
        tokens = await service.push_tokens.list_by_farmer(farmer_id)
        if not tokens:
            raise RuntimeError(f"No push tokens found for farmer {farmer_id}.")

        print("Sending to saved tokens:")
        for token in tokens:
            print(f"- {token.platform or 'unknown'} {token_label(token.expo_push_token)}")

        await service.send_message_notification(
            farmer_id=farmer_id,
            cattle_id=cattle_id,
            cattle_name=cattle_name,
            message=body,
        )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Send a manual CowX test notification.")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--farmer-id", type=UUID)
    target.add_argument("--token")
    target.add_argument("--latest", action="store_true")
    parser.add_argument("--title", default="CowX test notification")
    parser.add_argument("--body", default="If you see this, push delivery works.")
    parser.add_argument("--cattle-id", type=UUID, default=uuid4())
    parser.add_argument("--cattle-name", default="Test cow")
    args = parser.parse_args()

    if args.farmer_id:
        await send_to_farmer(
            farmer_id=args.farmer_id,
            body=args.body,
            cattle_id=args.cattle_id,
            cattle_name=args.cattle_name,
        )
        print("Notification request sent.")
        return

    token = args.token
    if args.latest:
        token = await latest_token()
        if not token:
            raise RuntimeError("No push tokens are saved in the database.")

    assert token
    print(f"Sending to {token_label(token)}")
    await send_raw_token(
        token=token,
        title=args.title,
        body=args.body,
        cattle_id=str(args.cattle_id),
    )
    print("Notification request sent.")


if __name__ == "__main__":
    asyncio.run(main())
