from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.db.redis import RedisDep
from app.db.session import AsyncSessionDep
from app.schemas.auth import (
    RefreshTokenRequest,
    SendCodeRequest,
    SendCodeResponse,
    TokenPair,
    VerifyCodeRequest,
)
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-code", response_model=SendCodeResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_code(
    payload: SendCodeRequest,
    redis: RedisDep,
    service: AuthService = Depends(get_auth_service),
) -> SendCodeResponse:
    return await service.send_code(redis, payload)


@router.post("/verify-code", response_model=TokenPair)
async def verify_code(
    payload: VerifyCodeRequest,
    session: AsyncSessionDep,
    redis: RedisDep,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return await service.verify_code(session, redis, payload)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshTokenRequest,
    session: AsyncSessionDep,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return await service.refresh(session, payload.refresh_token)

