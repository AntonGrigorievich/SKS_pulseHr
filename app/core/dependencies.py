from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_jwt_token
from app.db.session import AsyncSessionDep
from app.models.user import Role, User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    session: AsyncSessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    try:
        payload = decode_jwt_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user = await UserRepository().get_by_id(session, UUID(subject))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_hr(current_user: CurrentUser) -> User:
    if current_user.role != Role.HR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="HR role required")
    return current_user


async def require_employee(current_user: CurrentUser) -> User:
    return current_user


HRUser = Annotated[User, Depends(require_hr)]
EmployeeUser = Annotated[User, Depends(require_employee)]

