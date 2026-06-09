from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import DeliveryStatus, NotificationChannel


class NotificationSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    push_enabled: bool
    telegram_enabled: bool
    email_enabled: bool
    sms_enabled: bool
    telegram_chat_id: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime


class NotificationSettingsUpdate(BaseModel):
    push_enabled: bool | None = None
    telegram_enabled: bool | None = None
    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    telegram_chat_id: str | None = Field(default=None, max_length=128)
    email: str | None = Field(default=None, max_length=255)


class NotificationSubscriptionCreate(BaseModel):
    channel: NotificationChannel
    device_name: str | None = Field(default=None, max_length=255)
    destination: str = Field(min_length=1, max_length=512)


class NotificationSubscriptionRead(NotificationSubscriptionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NotificationCreate(BaseModel):
    survey_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    user_ids: list[UUID] = Field(min_length=1)
    channels: list[NotificationChannel] = Field(min_length=1)
    step_delay_seconds: int | None = Field(default=None, ge=0)
    stop_on_success: bool = True
    payload: dict = Field(default_factory=dict)


class NotificationDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_id: UUID
    user_id: UUID
    channel: NotificationChannel
    status: DeliveryStatus
    scheduled_at: datetime
    attempt_order: int
    destination: str
    provider_message_id: str | None
    error_message: str | None
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime
