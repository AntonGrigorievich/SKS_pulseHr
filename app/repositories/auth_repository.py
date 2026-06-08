from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import RefreshToken


class RefreshTokenRepository:
    async def create(
        self,
        session: AsyncSession,
        *,
        user_id,
        jti: str,
        expires_at: datetime,
        created_at: datetime,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
            created_at=created_at,
        )
        session.add(refresh_token)
        await session.flush()
        return refresh_token

    async def get_active_by_jti(self, session: AsyncSession, jti: str) -> RefreshToken | None:
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.jti == jti,
                RefreshToken.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, session: AsyncSession, refresh_token: RefreshToken, revoked_at: datetime) -> None:
        refresh_token.revoked_at = revoked_at
        await session.flush()

