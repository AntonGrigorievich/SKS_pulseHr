from __future__ import annotations

from json import JSONDecodeError
from pathlib import Path
import re
from types import new_class
from typing import Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import String, Text
from sqlalchemy.inspection import inspect
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.datastructures import FormData, UploadFile
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.db.redis import get_redis_client
from app.db.session import AsyncSessionLocal, engine
from app.models.user import Role, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import SendCodeRequest
from app.services.auth_service import get_auth_service

_WORD_BOUNDARY_RE = re.compile(r"(?<!^)(?=[A-Z])")
_TEMPLATES_DIR = Path(__file__).parent / "templates"


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        phone = _form_value(form, "username")
        code = _form_value(form, "password")
        if not phone or not code:
            return False

        redis = await get_redis_client()
        stored_code = await redis.get(_otp_code_key(phone))
        if stored_code is None:
            return False

        attempts_key = _otp_attempts_key(phone)
        attempts = await redis.incr(attempts_key)
        if attempts == 1:
            await redis.expire(attempts_key, settings.otp_ttl_seconds)
        if attempts > settings.otp_max_verify_attempts or stored_code != code:
            return False

        async with AsyncSessionLocal() as session:
            user = await UserRepository().get_by_phone(session, phone)
            if user is None or not user.is_active or user.role != Role.HR:
                return False

        await redis.delete(
            _otp_code_key(phone),
            _otp_attempts_key(phone),
            _otp_rate_key(phone),
        )
        request.session.update({"admin_user_id": str(user.id)})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        user_id = request.session.get("admin_user_id")
        if not isinstance(user_id, str):
            return False

        try:
            user_uuid = UUID(user_id)
        except ValueError:
            return False

        async with AsyncSessionLocal() as session:
            user = await session.get(User, user_uuid)
            return bool(user is not None and user.is_active and user.role == Role.HR)


def setup_admin(app: FastAPI) -> Admin:
    admin = Admin(
        app=app,
        engine=engine,
        title=f"{settings.app_name} Admin",
        templates_dir=str(_TEMPLATES_DIR),
        authentication_backend=AdminAuth(secret_key=settings.jwt_secret_key),
    )
    admin.admin.add_route(
        "/send-code",
        admin_send_code,
        methods=["POST"],
        name="send_code",
    )

    for view in _build_model_views():
        admin.add_view(view)

    return admin


async def admin_send_code(request: Request) -> Response:
    try:
        body = await request.json()
        payload = SendCodeRequest.model_validate(body)
    except (JSONDecodeError, ValidationError):
        return JSONResponse(
            {"detail": "Valid phone is required"},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    redis = await get_redis_client()
    try:
        result = await get_auth_service().send_code(redis, payload)
    except HTTPException as exc:
        return JSONResponse(
            {"detail": exc.detail},
            status_code=exc.status_code,
            headers=exc.headers,
        )

    return JSONResponse(result.model_dump(), status_code=status.HTTP_202_ACCEPTED)


def _build_model_views() -> list[type[ModelView]]:
    models = sorted(
        (mapper.class_ for mapper in Base.registry.mappers),
        key=lambda model: model.__tablename__,
    )
    return [_build_model_view(model) for model in models]


def _build_model_view(model: type[Base]) -> type[ModelView]:
    label = _model_label(model)
    attrs: dict[str, Any] = {
        "__module__": __name__,
        "name": label,
        "name_plural": _pluralize(label),
        "column_list": "__all__",
        "column_details_list": "__all__",
        "can_export": True,
        "can_view_details": True,
        "page_size": 50,
        "page_size_options": [25, 50, 100, 200],
    }
    searchable_columns = _searchable_columns(model)
    if searchable_columns:
        attrs["column_searchable_list"] = searchable_columns

    return new_class(
        f"{model.__name__}Admin",
        (ModelView,),
        {"model": model},
        lambda namespace: namespace.update(attrs),
    )


def _searchable_columns(model: type[Base]) -> list[Any]:
    mapper = inspect(model)
    return [
        getattr(model, column.key)
        for column in mapper.columns
        if isinstance(column.type, String | Text)
    ]


def _model_label(model: type[Base]) -> str:
    return _WORD_BOUNDARY_RE.sub(" ", model.__name__)


def _pluralize(label: str) -> str:
    if label.endswith("s"):
        return label
    if label.endswith("y"):
        return f"{label[:-1]}ies"
    return f"{label}s"


def _form_value(form: FormData, key: str) -> str:
    value = form.get(key)
    if value is None or isinstance(value, UploadFile):
        return ""
    return str(value).strip()


def _otp_code_key(phone: str) -> str:
    return f"otp:code:{phone}"


def _otp_rate_key(phone: str) -> str:
    return f"otp:rate:{phone}"


def _otp_attempts_key(phone: str) -> str:
    return f"otp:attempts:{phone}"
