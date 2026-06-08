from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, String
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
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    created_surveys = relationship("Survey", back_populates="created_by")
    survey_assignments = relationship("SurveyAssignment", back_populates="user")
    survey_responses = relationship("SurveyResponse", back_populates="user")
    notification_settings = relationship("NotificationSettings", back_populates="user", uselist=False)
