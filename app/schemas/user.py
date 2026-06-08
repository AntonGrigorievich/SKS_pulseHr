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

