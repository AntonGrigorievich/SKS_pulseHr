from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create(self, session: AsyncSession, payload: UserCreate):
        existing = await self.repository.get_by_phone(session, payload.phone)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this phone already exists",
            )

        try:
            user = await self.repository.create(session, payload)
            await session.commit()
            return user
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this phone already exists",
            ) from exc

    async def get(self, session: AsyncSession, user_id: UUID):
        user = await self.repository.get_by_id(session, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    async def list(self, session: AsyncSession, *, limit: int = 100, offset: int = 0):
        if limit < 1 or limit > 500:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid limit")
        if offset < 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid offset")
        return await self.repository.list(session, limit=limit, offset=offset)

    async def update(self, session: AsyncSession, user_id: UUID, payload: UserUpdate):
        user = await self.get(session, user_id)
        if payload.phone is not None:
            existing = await self.repository.get_by_phone(session, payload.phone)
            if existing is not None and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this phone already exists",
                )

        try:
            updated = await self.repository.update(session, user, payload)
            await session.commit()
            return updated
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this phone already exists",
            ) from exc

    async def delete(self, session: AsyncSession, user_id: UUID) -> None:
        user = await self.get(session, user_id)
        await self.repository.delete(session, user)
        await session.commit()


def get_user_service() -> UserService:
    return UserService(UserRepository())

