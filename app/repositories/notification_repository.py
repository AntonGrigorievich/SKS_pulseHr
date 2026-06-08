from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationSettings,
    NotificationSubscription,
)


class NotificationRepository:
    async def get_settings(self, session: AsyncSession, user_id: UUID) -> NotificationSettings | None:
        result = await session.execute(select(NotificationSettings).where(NotificationSettings.user_id == user_id))
        return result.scalar_one_or_none()

    async def list_subscriptions(self, session: AsyncSession, user_id: UUID) -> list[NotificationSubscription]:
        result = await session.execute(
            select(NotificationSubscription)
            .where(NotificationSubscription.user_id == user_id)
            .order_by(NotificationSubscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_notification(self, session: AsyncSession, notification: Notification) -> Notification:
        session.add(notification)
        await session.flush()
        await session.refresh(notification)
        return notification

    async def create_delivery(self, session: AsyncSession, delivery: NotificationDelivery) -> NotificationDelivery:
        session.add(delivery)
        await session.flush()
        return delivery

