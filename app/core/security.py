from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.core.config import settings


def utcnow() -> datetime:
    return datetime.now(UTC)


def create_jwt_token(
    *,
    subject: UUID,
    token_type: str,
    expires_delta: timedelta,
    jti: str | None = None,
) -> tuple[str, datetime]:
    expires_at = utcnow() + expires_delta
    payload: dict[str, str | int] = {
        "sub": str(subject),
        "type": token_type,
        "exp": int(expires_at.timestamp()),
        "iat": int(utcnow().timestamp()),
    }
    if jti is not None:
        payload["jti"] = jti

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_jwt_token(token: str) -> dict[str, str | int]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

