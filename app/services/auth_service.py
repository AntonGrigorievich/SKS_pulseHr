from __future__ import annotations

import logging
import secrets
from datetime import timedelta
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_jwt_token, decode_jwt_token, utcnow
from app.models.user import Role
from app.repositories.auth_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import SendCodeRequest, SendCodeResponse, TokenPair, VerifyCodeRequest
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
    ) -> None:
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository

    async def send_code(self, redis: Redis, payload: SendCodeRequest) -> SendCodeResponse:
        rate_key = self._rate_key(payload.phone)
        allowed = await redis.set(rate_key, "1", ex=settings.otp_rate_limit_seconds, nx=True)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="OTP was requested too recently",
            )

        code = f"{secrets.randbelow(1_000_000):06d}"
        await redis.set(self._code_key(payload.phone), code, ex=settings.otp_ttl_seconds)
        await redis.delete(self._attempts_key(payload.phone))

        logger.info("PulseHR OTP code for %s: %s", payload.phone, code)
        print(f"PulseHR OTP code for {payload.phone}: {code}", flush=True)

        return SendCodeResponse(
            message="OTP code generated",
            expires_in_seconds=settings.otp_ttl_seconds,
        )

    async def verify_code(
        self,
        session: AsyncSession,
        redis: Redis,
        payload: VerifyCodeRequest,
    ) -> TokenPair:
        stored_code = await redis.get(self._code_key(payload.phone))
        if stored_code is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired or not found")

        attempts_key = self._attempts_key(payload.phone)
        attempts = await redis.incr(attempts_key)
        if attempts == 1:
            await redis.expire(attempts_key, settings.otp_ttl_seconds)
        if attempts > settings.otp_max_verify_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP verification attempts",
            )

        if payload.code != stored_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code")

        await redis.delete(self._code_key(payload.phone), attempts_key, self._rate_key(payload.phone))

        user = await self.user_repository.get_by_phone(session, payload.phone)
        if user is None:
            user = await self.user_repository.create(
                session,
                UserCreate(phone=payload.phone, role=Role.EMPLOYEE),
            )

        token_pair = await self._issue_token_pair(session, user.id)
        await session.commit()
        return token_pair

    async def refresh(self, session: AsyncSession, refresh_token: str) -> TokenPair:
        try:
            payload = decode_jwt_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        jti = payload.get("jti")
        subject = payload.get("sub")
        if not isinstance(jti, str) or not isinstance(subject, str):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        persisted_token = await self.refresh_token_repository.get_active_by_jti(session, jti)
        if persisted_token is None or persisted_token.expires_at <= utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is inactive")

        await self.refresh_token_repository.revoke(session, persisted_token, utcnow())
        token_pair = await self._issue_token_pair(session, UUID(subject))
        await session.commit()
        return token_pair

    async def _issue_token_pair(self, session: AsyncSession, user_id: UUID) -> TokenPair:
        access_token, _ = create_jwt_token(
            subject=user_id,
            token_type="access",
            expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        )

        refresh_jti = secrets.token_hex(16)
        refresh_token, refresh_expires_at = create_jwt_token(
            subject=user_id,
            token_type="refresh",
            expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
            jti=refresh_jti,
        )
        await self.refresh_token_repository.create(
            session,
            user_id=user_id,
            jti=refresh_jti,
            expires_at=refresh_expires_at,
            created_at=utcnow(),
        )

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    def _code_key(phone: str) -> str:
        return f"otp:code:{phone}"

    @staticmethod
    def _rate_key(phone: str) -> str:
        return f"otp:rate:{phone}"

    @staticmethod
    def _attempts_key(phone: str) -> str:
        return f"otp:attempts:{phone}"


def get_auth_service() -> AuthService:
    return AuthService(UserRepository(), RefreshTokenRepository())

