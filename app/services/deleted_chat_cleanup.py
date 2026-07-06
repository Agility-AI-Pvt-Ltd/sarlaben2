import asyncio
import logging

from app.database.session import SessionLocal
from app.repositories.deleted_chat_repository import DeletedChatRepository

logger = logging.getLogger(__name__)

DELETED_CHAT_CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60


async def run_deleted_chat_cleanup(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            async with SessionLocal() as db:
                deleted_count = await DeletedChatRepository(db).purge_expired()
                if deleted_count:
                    logger.info(
                        "Purged %s expired deleted chat messages",
                        deleted_count,
                    )
        except Exception:
            logger.warning("Deleted chat cleanup failed", exc_info=True)

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=DELETED_CHAT_CLEANUP_INTERVAL_SECONDS,
            )
        except TimeoutError:
            continue
