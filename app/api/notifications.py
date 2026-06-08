from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.dependencies import EmployeeUser, HRUser
from app.db.session import AsyncSessionDep
from app.schemas.notification import (
    NotificationCreate,
    NotificationDeliveryRead,
    NotificationSettingsRead,
    NotificationSettingsUpdate,
    NotificationSubscriptionCreate,
    NotificationSubscriptionRead,
)
from app.services.notification_service import NotificationService, get_notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/settings", response_model=NotificationSettingsRead)
async def get_settings(
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.get_settings(session, current_user)


@router.patch("/settings", response_model=NotificationSettingsRead)
async def update_settings(
    payload: NotificationSettingsUpdate,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.update_settings(session, current_user, payload)


@router.get("/subscriptions", response_model=list[NotificationSubscriptionRead])
async def list_subscriptions(
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.list_subscriptions(session, current_user)


@router.post("/subscriptions", response_model=NotificationSubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: NotificationSubscriptionCreate,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.create_subscription(session, current_user, payload)


@router.post("/send", response_model=list[NotificationDeliveryRead])
async def send_notification(
    payload: NotificationCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.send(session, payload)

