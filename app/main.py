from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.admin import setup_admin
from app.api.router import api_router
from app.core.config import settings
from app.db.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


setup_admin(app)
app.include_router(api_router, prefix=settings.api_prefix)
