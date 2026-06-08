from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.db.session import AsyncSessionDep
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: AsyncSessionDep,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.create(session, payload)


@router.get("", response_model=list[UserRead])
async def list_users(
    session: AsyncSessionDep,
    limit: int = 100,
    offset: int = 0,
    service: UserService = Depends(get_user_service),
) -> list[UserRead]:
    return await service.list(session, limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID,
    session: AsyncSessionDep,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.get(session, user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    session: AsyncSessionDep,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.update(session, user_id, payload)


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    session: AsyncSessionDep,
    service: UserService = Depends(get_user_service),
) -> None:
    await service.delete(session, user_id)

