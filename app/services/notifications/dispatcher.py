from __future__ import annotations

import logging
from collections.abc import Mapping
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.models.notification import DeliveryStatus, NotificationChannel, NotificationDelivery
from app.repositories.notification_repository import NotificationRepository
from app.services.notifications.providers import (
    NotificationProvider,
    ProviderError,
    ProviderSendResult,
    build_notification_providers,
)

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    def __init__(
        self,
        repository: NotificationRepository | None = None,
        providers: Mapping[NotificationChannel, NotificationProvider] | None = None,
    ) -> None:
        self.repository = repository or NotificationRepository()
        self.providers = providers or build_notification_providers()

    async def dispatch_due(self, session: AsyncSession, *, limit: int = 50) -> int:
        deliveries = await self.repository.claim_due_deliveries(
            session,
            due_at=utcnow(),
            limit=limit,
        )
        if not deliveries:
            await session.rollback()
            return 0

        delivery_ids = [delivery.id for delivery in deliveries]
        await session.commit()

        for delivery_id in delivery_ids:
            await self.dispatch_one(session, delivery_id)
        return len(delivery_ids)

    async def dispatch_one(self, session: AsyncSession, delivery_id: UUID) -> None:
        delivery = await self.repository.get_delivery_for_dispatch(session, delivery_id)
        if delivery is None or delivery.status != DeliveryStatus.SENDING:
            await session.rollback()
            return

        if await self._cancel_if_survey_completed(session, delivery):
            await session.commit()
            return

        if await self._cancel_if_previous_delivery_succeeded(session, delivery):
            await session.commit()
            return

        provider = self.providers.get(delivery.channel)
        if not self._provider_can_send(provider):
            delivery.status = DeliveryStatus.SKIPPED
            delivery.error_message = "Provider is not configured"
            await session.commit()
            return

        send_kwargs = {
            "destination": delivery.destination,
            "title": delivery.notification.title,
            "body": delivery.notification.body,
            "payload": delivery.notification.payload,
        }
        await session.commit()

        try:
            result = await provider.send(**send_kwargs)
        except ProviderError as exc:
            await self._mark_failed(session, delivery_id, str(exc))
            return
        except Exception as exc:
            logger.exception("Unexpected notification provider error")
            await self._mark_failed(session, delivery_id, str(exc))
            return

        await self._mark_sent(session, delivery_id, result)

    async def _cancel_if_survey_completed(
        self,
        session: AsyncSession,
        delivery: NotificationDelivery,
    ) -> bool:
        survey_id = delivery.notification.survey_id
        if survey_id is None:
            return False

        if not await self.repository.has_completed_survey(
            session,
            survey_id=survey_id,
            user_id=delivery.user_id,
        ):
            return False

        reason = "Survey already completed"
        delivery.status = DeliveryStatus.CANCELLED
        delivery.error_message = reason
        await self.repository.cancel_pending_deliveries(
            session,
            notification_id=delivery.notification_id,
            user_id=delivery.user_id,
            reason=reason,
            exclude_delivery_id=delivery.id,
        )
        return True

    async def _cancel_if_previous_delivery_succeeded(
        self,
        session: AsyncSession,
        delivery: NotificationDelivery,
    ) -> bool:
        if not delivery.notification.stop_on_success:
            return False

        if not await self.repository.has_sent_delivery_before(
            session,
            notification_id=delivery.notification_id,
            user_id=delivery.user_id,
            attempt_order=delivery.attempt_order,
        ):
            return False

        reason = "Previous delivery succeeded"
        delivery.status = DeliveryStatus.CANCELLED
        delivery.error_message = reason
        await self.repository.cancel_pending_deliveries(
            session,
            notification_id=delivery.notification_id,
            user_id=delivery.user_id,
            reason=reason,
            exclude_delivery_id=delivery.id,
        )
        return True

    async def _mark_failed(
        self,
        session: AsyncSession,
        delivery_id: UUID,
        error_message: str,
    ) -> None:
        delivery = await self.repository.get_delivery_for_dispatch(session, delivery_id)
        if delivery is None or delivery.status != DeliveryStatus.SENDING:
            await session.rollback()
            return

        delivery.status = DeliveryStatus.FAILED
        delivery.error_message = error_message[:2000]
        await session.commit()
        logger.warning("Notification delivery %s failed: %s", delivery_id, error_message)

    async def _mark_sent(
        self,
        session: AsyncSession,
        delivery_id: UUID,
        result: ProviderSendResult,
    ) -> None:
        delivery = await self.repository.get_delivery_for_dispatch(session, delivery_id)
        if delivery is None or delivery.status != DeliveryStatus.SENDING:
            await session.rollback()
            return

        delivery.status = DeliveryStatus.SENT
        delivery.sent_at = utcnow()
        delivery.provider_message_id = result.provider_message_id

        if delivery.notification.stop_on_success:
            await self.repository.cancel_pending_deliveries(
                session,
                notification_id=delivery.notification_id,
                user_id=delivery.user_id,
                reason="Previous delivery succeeded",
                exclude_delivery_id=delivery.id,
            )

        await session.commit()
        logger.info("Notification delivery %s sent", delivery_id)

    @staticmethod
    def _provider_can_send(provider: NotificationProvider | None) -> bool:
        return bool(provider and provider.is_configured)
