from __future__ import annotations

import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.services.notifications.dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)


class NotificationWorker:
    def __init__(
        self,
        dispatcher: NotificationDispatcher | None = None,
        *,
        poll_interval_seconds: int = 5,
        batch_size: int = 50,
    ) -> None:
        self.dispatcher = dispatcher or NotificationDispatcher()
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size

    async def run_forever(self) -> None:
        logger.info("PulseHR notification worker started")
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    processed = await self.dispatcher.dispatch_due(
                        session,
                        limit=self.batch_size,
                    )
            except Exception:
                logger.exception("Notification worker poll failed")
                await asyncio.sleep(self.poll_interval_seconds)
                continue

            if processed == 0:
                await asyncio.sleep(self.poll_interval_seconds)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    worker = NotificationWorker()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
