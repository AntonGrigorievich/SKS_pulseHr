from __future__ import annotations

from fastapi import APIRouter

from app.api import auth, users

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(auth.router)

