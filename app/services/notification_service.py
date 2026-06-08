from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.models.notification import (
    DeliveryStatus,
    Notification,
    NotificationDelivery,
    NotificationSettings,
    NotificationSubscription,
)
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    NotificationCreate,
    NotificationSettingsUpdate,
    NotificationSubscriptionCreate,
)

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository

    async def get_settings(self, session: AsyncSession, current_user: User) -> NotificationSettings:
        settings = await self.repository.get_settings(session, current_user.id)
        if settings is None:
            settings = NotificationSettings(user_id=current_user.id)
            session.add(settings)
            await session.commit()
            await session.refresh(settings)
        return settings

    async def update_settings(
        self,
        session: AsyncSession,
        current_user: User,
        payload: NotificationSettingsUpdate,
    ) -> NotificationSettings:
        settings = await self.get_settings(session, current_user)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        await session.commit()
        await session.refresh(settings)
        return settings

    async def list_subscriptions(self, session: AsyncSession, current_user: User) -> list[NotificationSubscription]:
        return await self.repository.list_subscriptions(session, current_user.id)

    async def create_subscription(
        self,
        session: AsyncSession,
        current_user: User,
        payload: NotificationSubscriptionCreate,
    ) -> NotificationSubscription:
        subscription = NotificationSubscription(user_id=current_user.id, **payload.model_dump())
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        return subscription

    async def send(self, session: AsyncSession, payload: NotificationCreate) -> list[NotificationDelivery]:
        notification = await self.repository.create_notification(
            session,
            Notification(
                survey_id=payload.survey_id,
                title=payload.title,
                body=payload.body,
                payload=payload.payload,
            ),
        )
        deliveries: list[NotificationDelivery] = []
        for user_id in payload.user_ids:
            for channel in payload.channels:
                logger.info("PulseHR notification via %s to %s: %s", channel.value, user_id, payload.title)
                delivery = await self.repository.create_delivery(
                    session,
                    NotificationDelivery(
                        notification_id=notification.id,
                        user_id=user_id,
                        channel=channel,
                        status=DeliveryStatus.SENT,
                        sent_at=utcnow(),
                    ),
                )
                deliveries.append(delivery)
        await session.commit()
        return deliveries


def get_notification_service() -> NotificationService:
    return NotificationService(NotificationRepository())

