from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.notification import (
    DeliveryStatus,
    Notification,
    NotificationDelivery,
    NotificationSettings,
    NotificationSubscription,
)
from app.models.response import ResponseStatus, SurveyResponse
from app.models.survey import AssignmentStatus, SurveyAssignment
from app.models.user import User


class NotificationRepository:
    async def list_users(self, session: AsyncSession, user_ids: Sequence[UUID]) -> list[User]:
        result = await session.execute(select(User).where(User.id.in_(user_ids)))
        return list(result.scalars().all())

    async def get_settings(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> NotificationSettings | None:
        result = await session.execute(
            select(NotificationSettings).where(NotificationSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_settings_for_users(
        self,
        session: AsyncSession,
        user_ids: Sequence[UUID],
    ) -> dict[UUID, NotificationSettings]:
        result = await session.execute(
            select(NotificationSettings).where(NotificationSettings.user_id.in_(user_ids))
        )
        return {settings.user_id: settings for settings in result.scalars().all()}

    async def list_subscriptions(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> list[NotificationSubscription]:
        result = await session.execute(
            select(NotificationSubscription)
            .where(NotificationSubscription.user_id == user_id)
            .order_by(NotificationSubscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_active_subscriptions_for_users(
        self,
        session: AsyncSession,
        user_ids: Sequence[UUID],
    ) -> dict[UUID, list[NotificationSubscription]]:
        result = await session.execute(
            select(NotificationSubscription)
            .where(
                NotificationSubscription.user_id.in_(user_ids),
                NotificationSubscription.is_active.is_(True),
            )
            .order_by(NotificationSubscription.created_at.desc())
        )
        subscriptions_by_user_id: dict[UUID, list[NotificationSubscription]] = defaultdict(list)
        for subscription in result.scalars().all():
            subscriptions_by_user_id[subscription.user_id].append(subscription)
        return subscriptions_by_user_id

    async def create_notification(
        self,
        session: AsyncSession,
        notification: Notification,
    ) -> Notification:
        session.add(notification)
        await session.flush()
        await session.refresh(notification)
        return notification

    async def create_delivery(
        self,
        session: AsyncSession,
        delivery: NotificationDelivery,
    ) -> NotificationDelivery:
        session.add(delivery)
        await session.flush()
        return delivery

    async def claim_due_deliveries(
        self,
        session: AsyncSession,
        *,
        due_at: datetime,
        limit: int,
    ) -> list[NotificationDelivery]:
        result = await session.execute(
            select(NotificationDelivery)
            .where(
                NotificationDelivery.status == DeliveryStatus.PENDING,
                NotificationDelivery.scheduled_at <= due_at,
            )
            .order_by(
                NotificationDelivery.scheduled_at.asc(),
                NotificationDelivery.created_at.asc(),
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        deliveries = list(result.scalars().all())
        for delivery in deliveries:
            delivery.status = DeliveryStatus.SENDING
        await session.flush()
        return deliveries

    async def get_delivery_for_dispatch(
        self,
        session: AsyncSession,
        delivery_id: UUID,
    ) -> NotificationDelivery | None:
        result = await session.execute(
            select(NotificationDelivery)
            .where(NotificationDelivery.id == delivery_id)
            .options(
                selectinload(NotificationDelivery.notification),
                selectinload(NotificationDelivery.user),
            )
        )
        return result.scalar_one_or_none()

    async def has_sent_delivery_before(
        self,
        session: AsyncSession,
        *,
        notification_id: UUID,
        user_id: UUID,
        attempt_order: int,
    ) -> bool:
        result = await session.execute(
            select(NotificationDelivery.id)
            .where(
                NotificationDelivery.notification_id == notification_id,
                NotificationDelivery.user_id == user_id,
                NotificationDelivery.attempt_order < attempt_order,
                NotificationDelivery.status == DeliveryStatus.SENT,
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def cancel_pending_deliveries(
        self,
        session: AsyncSession,
        *,
        notification_id: UUID,
        user_id: UUID,
        reason: str,
        exclude_delivery_id: UUID | None = None,
    ) -> int:
        result = await session.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.notification_id == notification_id,
                NotificationDelivery.user_id == user_id,
                NotificationDelivery.status == DeliveryStatus.PENDING,
            )
        )
        cancelled = 0
        for delivery in result.scalars().all():
            if exclude_delivery_id is not None and delivery.id == exclude_delivery_id:
                continue
            delivery.status = DeliveryStatus.CANCELLED
            delivery.error_message = reason
            cancelled += 1
        await session.flush()
        return cancelled

    async def has_completed_survey(
        self,
        session: AsyncSession,
        *,
        survey_id: UUID,
        user_id: UUID,
    ) -> bool:
        response_result = await session.execute(
            select(SurveyResponse.id)
            .where(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.user_id == user_id,
                SurveyResponse.status == ResponseStatus.SUBMITTED,
            )
            .limit(1)
        )
        if response_result.scalar_one_or_none() is not None:
            return True

        assignment_result = await session.execute(
            select(SurveyAssignment.id)
            .where(
                SurveyAssignment.survey_id == survey_id,
                SurveyAssignment.user_id == user_id,
                SurveyAssignment.status == AssignmentStatus.SUBMITTED,
            )
            .limit(1)
        )
        return assignment_result.scalar_one_or_none() is not None
