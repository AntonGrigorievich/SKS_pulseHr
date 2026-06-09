from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from app.models.notification import (
    NotificationChannel,
    NotificationSettings,
    NotificationSubscription,
)
from app.models.user import User
from app.services.notifications.providers import NotificationProvider


@dataclass(frozen=True)
class DeliveryPlan:
    user_id: UUID
    channel: NotificationChannel
    destination: str
    scheduled_at: datetime
    attempt_order: int


class NotificationSequenceBuilder:
    def __init__(self, providers: Mapping[NotificationChannel, NotificationProvider]) -> None:
        self.providers = providers

    def build(
        self,
        *,
        user: User,
        settings: NotificationSettings | None,
        subscriptions: Sequence[NotificationSubscription],
        channels: Sequence[NotificationChannel],
        now: datetime,
        step_delay_seconds: int,
    ) -> list[DeliveryPlan]:
        available_channels = [
            (channel, destination)
            for channel in channels
            if (destination := self._destination(user, settings, subscriptions, channel))
            and self._is_channel_available(settings, channel)
            and self._is_provider_configured(channel)
        ]

        return [
            DeliveryPlan(
                user_id=user.id,
                channel=channel,
                destination=destination,
                scheduled_at=now + timedelta(seconds=step_delay_seconds * index),
                attempt_order=index + 1,
            )
            for index, (channel, destination) in enumerate(available_channels)
        ]

    def _is_provider_configured(self, channel: NotificationChannel) -> bool:
        provider = self.providers.get(channel)
        return bool(provider and provider.is_configured)

    @staticmethod
    def _is_channel_available(
        settings: NotificationSettings | None,
        channel: NotificationChannel,
    ) -> bool:
        if channel == NotificationChannel.TELEGRAM:
            return bool(settings and settings.telegram_enabled)
        if channel == NotificationChannel.EMAIL:
            return bool(settings and settings.email_enabled)
        if channel == NotificationChannel.SMS:
            return settings.sms_enabled if settings else True
        return False

    def _destination(
        self,
        user: User,
        settings: NotificationSettings | None,
        subscriptions: Iterable[NotificationSubscription],
        channel: NotificationChannel,
    ) -> str | None:
        active_subscription = self._subscription_destination(subscriptions, channel)

        if channel == NotificationChannel.TELEGRAM:
            return (settings.telegram_chat_id if settings else None) or active_subscription
        if channel == NotificationChannel.EMAIL:
            return (settings.email if settings else None) or active_subscription
        if channel == NotificationChannel.SMS:
            return active_subscription or user.phone
        return None

    @staticmethod
    def _subscription_destination(
        subscriptions: Iterable[NotificationSubscription],
        channel: NotificationChannel,
    ) -> str | None:
        for subscription in subscriptions:
            if (
                subscription.channel == channel
                and subscription.is_active
                and subscription.destination
            ):
                return subscription.destination
        return None
