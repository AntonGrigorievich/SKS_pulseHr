from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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
from app.services.notifications.providers import build_notification_providers
from app.services.notifications.sequence import NotificationSequenceBuilder

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        repository: NotificationRepository,
        sequence_builder: NotificationSequenceBuilder | None = None,
    ) -> None:
        self.repository = repository
        self.sequence_builder = sequence_builder or NotificationSequenceBuilder(
            build_notification_providers()
        )

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

    async def list_subscriptions(
        self,
        session: AsyncSession,
        current_user: User,
    ) -> list[NotificationSubscription]:
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

    async def send(
        self,
        session: AsyncSession,
        payload: NotificationCreate,
    ) -> list[NotificationDelivery]:
        user_ids = list(dict.fromkeys(payload.user_ids))
        users = await self.repository.list_users(session, user_ids)
        users_by_id = {user.id: user for user in users}
        missing_user_ids = [str(user_id) for user_id in user_ids if user_id not in users_by_id]
        if missing_user_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Users not found", "user_ids": missing_user_ids},
            )

        step_delay_seconds = (
            payload.step_delay_seconds
            if payload.step_delay_seconds is not None
            else settings.notification_step_delay_seconds
        )
        notification = await self.repository.create_notification(
            session,
            Notification(
                survey_id=payload.survey_id,
                title=payload.title,
                body=payload.body,
                payload=payload.payload,
                stop_on_success=payload.stop_on_success,
                step_delay_seconds=step_delay_seconds,
            ),
        )
        settings_by_user_id = await self.repository.list_settings_for_users(session, user_ids)
        subscriptions_by_user_id = await self.repository.list_active_subscriptions_for_users(
            session,
            user_ids,
        )

        now = utcnow()
        deliveries: list[NotificationDelivery] = []
        for user_id in user_ids:
            user = users_by_id[user_id]
            plans = self.sequence_builder.build(
                user=user,
                settings=settings_by_user_id.get(user_id),
                subscriptions=subscriptions_by_user_id.get(user_id, []),
                channels=payload.channels,
                now=now,
                step_delay_seconds=step_delay_seconds,
            )
            for plan in plans:
                delivery = await self.repository.create_delivery(
                    session,
                    NotificationDelivery(
                        notification_id=notification.id,
                        user_id=plan.user_id,
                        channel=plan.channel,
                        status=DeliveryStatus.PENDING,
                        scheduled_at=plan.scheduled_at,
                        attempt_order=plan.attempt_order,
                        destination=plan.destination,
                    ),
                )
                deliveries.append(delivery)

        logger.info(
            "Scheduled %s PulseHR notification deliveries for notification %s",
            len(deliveries),
            notification.id,
        )
        await session.commit()
        return deliveries


def get_notification_service() -> NotificationService:
    return NotificationService(NotificationRepository())
