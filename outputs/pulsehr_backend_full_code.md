# PulseHR Backend MVP

## Project Tree

```text
.
.env
.env.example
.gitignore
Dockerfile
alembic.ini
    env.py
    script.py.mako
        20260608_0001_create_users_and_refresh_tokens.py
    __init__.py
        __init__.py
        auth.py
        router.py
        users.py
        __init__.py
        config.py
        security.py
        __init__.py
        base.py
        redis.py
        session.py
    main.py
        __init__.py
        auth.py
        user.py
        __init__.py
        auth_repository.py
        user_repository.py
        __init__.py
        auth.py
        user.py
        __init__.py
        auth_service.py
        user_service.py
docker-compose.yml
pyproject.toml
requirements.txt
```

## .env

```text
APP_NAME=PulseHR
APP_ENV=local
DEBUG=true
API_PREFIX=

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=pulsehr
POSTGRES_USER=pulsehr
POSTGRES_PASSWORD=pulsehr_password

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

OTP_TTL_SECONDS=300
OTP_RATE_LIMIT_SECONDS=60
OTP_MAX_VERIFY_ATTEMPTS=5

```

## .env.example

```text
APP_NAME=PulseHR
APP_ENV=local
DEBUG=true
API_PREFIX=

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=pulsehr
POSTGRES_USER=pulsehr
POSTGRES_PASSWORD=pulsehr_password

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

OTP_TTL_SECONDS=300
OTP_RATE_LIMIT_SECONDS=60
OTP_MAX_VERIFY_ATTEMPTS=5

```

## .gitignore

```text
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
.venv/
venv/
.env.local
postgres_data/
redis_data/


```

## Dockerfile

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


```

## docker-compose.yml

```yaml
services:
  api:
    build: .
    container_name: pulsehr-api
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    volumes:
      - .:/app

  postgres:
    image: postgres:16-alpine
    container_name: pulsehr-postgres
    environment:
      POSTGRES_DB: pulsehr
      POSTGRES_USER: pulsehr
      POSTGRES_PASSWORD: pulsehr_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pulsehr -d pulsehr"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: pulsehr-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  postgres_data:
  redis_data:


```

## pyproject.toml

```toml
[project]
name = "pulsehr-backend"
version = "0.1.0"
description = "PulseHR backend MVP"
requires-python = ">=3.12"
dependencies = [
    "alembic==1.13.3",
    "asyncpg==0.29.0",
    "fastapi==0.115.0",
    "greenlet==3.1.1",
    "pydantic==2.9.2",
    "pydantic-settings==2.5.2",
    "pyjwt==2.9.0",
    "python-dotenv==1.0.1",
    "redis==5.0.8",
    "sqlalchemy==2.0.35",
    "uvicorn[standard]==0.30.6"
]

[project.optional-dependencies]
dev = [
    "ruff==0.6.8"
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

```

## requirements.txt

```text
alembic==1.13.3
asyncpg==0.29.0
fastapi==0.115.0
greenlet==3.1.1
pydantic==2.9.2
pydantic-settings==2.5.2
pyjwt==2.9.0
python-dotenv==1.0.1
redis==5.0.8
sqlalchemy==2.0.35
uvicorn[standard]==0.30.6

```

## alembic.ini

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://pulsehr:pulsehr_password@postgres:5432/pulsehr

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S


```

## alembic/env.py

```python
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base
from app.models import auth, user  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


```

## alembic/script.py.mako

```python
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}


```

## alembic/versions/20260608_0001_create_users_and_refresh_tokens.py

```python
"""create users and refresh tokens

Revision ID: 20260608_0001
Revises:
Create Date: 2026-06-08 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260608_0001"
down_revision = None
branch_labels = None
depends_on = None

role_enum = postgresql.ENUM("HR", "EMPLOYEE", name="role", create_type=False)


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE role AS ENUM ('HR', 'EMPLOYEE');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", role_enum, nullable=False, server_default=sa.text("'EMPLOYEE'")),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone", name="uq_users_phone"),
    )
    op.create_index("ix_users_phone", "users", ["phone"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti", name="uq_refresh_tokens_jti"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_table("users")
    role_enum.drop(op.get_bind(), checkfirst=True)

```

## app/__init__.py

```python


```

## app/main.py

```python
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

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


app.include_router(api_router, prefix=settings.api_prefix)


```

## app/api/__init__.py

```python


```

## app/api/router.py

```python
from __future__ import annotations

from fastapi import APIRouter

from app.api import auth, users

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(auth.router)


```

## app/api/users.py

```python
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


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    session: AsyncSessionDep,
    service: UserService = Depends(get_user_service),
) -> None:
    await service.delete(session, user_id)


```

## app/api/auth.py

```python
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


```

## app/core/__init__.py

```python


```

## app/core/config.py

```python
from __future__ import annotations

from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PulseHR"
    app_env: str = "local"
    debug: bool = False
    api_prefix: str = ""

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "pulsehr"
    postgres_user: str = "pulsehr"
    postgres_password: str = "pulsehr_password"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    jwt_secret_key: str = Field(min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 30

    otp_ttl_seconds: int = 300
    otp_rate_limit_seconds: int = 60
    otp_max_verify_attempts: int = 5

    @cached_property
    def database_url(self) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @cached_property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()

```

## app/core/security.py

```python
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


```

## app/db/__init__.py

```python


```

## app/db/base.py

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


```

## app/db/session.py

```python
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]


```

## app/db/redis.py

```python
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.core.config import settings

_redis: Redis | None = None


async def get_redis_client() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def get_redis() -> AsyncIterator[Redis]:
    yield await get_redis_client()


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


RedisDep = Annotated[Redis, Depends(get_redis)]


```

## app/models/__init__.py

```python
from app.models.auth import RefreshToken
from app.models.user import Role, User

__all__ = ["RefreshToken", "Role", "User"]


```

## app/models/user.py

```python
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Role(str, enum.Enum):
    HR = "HR"
    EMPLOYEE = "EMPLOYEE"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), default=Role.EMPLOYEE, nullable=False)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


```

## app/models/auth.py

```python
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


```

## app/repositories/__init__.py

```python


```

## app/repositories/user_repository.py

```python
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    async def create(self, session: AsyncSession, payload: UserCreate) -> User:
        user = User(**payload.model_dump())
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    async def get_by_id(self, session: AsyncSession, user_id: UUID) -> User | None:
        return await session.get(User, user_id)

    async def get_by_phone(self, session: AsyncSession, phone: str) -> User | None:
        result = await session.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def list(self, session: AsyncSession, *, limit: int, offset: int) -> list[User]:
        result = await session.execute(
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def update(self, session: AsyncSession, user: User, payload: UserUpdate) -> User:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await session.flush()
        await session.refresh(user)
        return user

    async def delete(self, session: AsyncSession, user: User) -> None:
        await session.delete(user)
        await session.flush()


```

## app/repositories/auth_repository.py

```python
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


```

## app/schemas/__init__.py

```python


```

## app/schemas/user.py

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import Role


class UserBase(BaseModel):
    phone: str = Field(min_length=5, max_length=32, examples=["+79991234567"])
    full_name: str | None = Field(default=None, max_length=255, examples=["Ivan Petrov"])
    role: Role = Role.EMPLOYEE
    department: str | None = Field(default=None, max_length=255, examples=["Engineering"])


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    phone: str | None = Field(default=None, min_length=5, max_length=32)
    full_name: str | None = Field(default=None, max_length=255)
    role: Role | None = None
    department: str | None = Field(default=None, max_length=255)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


```

## app/schemas/auth.py

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class SendCodeRequest(BaseModel):
    phone: str = Field(min_length=5, max_length=32, examples=["+79991234567"])


class SendCodeResponse(BaseModel):
    message: str
    expires_in_seconds: int


class VerifyCodeRequest(BaseModel):
    phone: str = Field(min_length=5, max_length=32)
    code: str = Field(pattern=r"^\d{6}$", examples=["123456"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


```

## app/services/__init__.py

```python


```

## app/services/user_service.py

```python
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


```

## app/services/auth_service.py

```python
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


```
