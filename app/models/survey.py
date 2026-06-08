from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SurveyStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class AssignmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUBMITTED = "SUBMITTED"


class Survey(TimestampMixin, Base):
    __tablename__ = "surveys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SurveyStatus] = mapped_column(
        Enum(SurveyStatus, name="survey_status"),
        default=SurveyStatus.DRAFT,
        nullable=False,
    )
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_by = relationship("User", back_populates="created_surveys")
    questions = relationship(
        "Question",
        back_populates="survey",
        cascade="all, delete-orphan",
        order_by="Question.position",
    )
    rules = relationship(
        "SurveyRule",
        back_populates="survey",
        cascade="all, delete-orphan",
        order_by="SurveyRule.priority",
    )
    assignments = relationship("SurveyAssignment", back_populates="survey", cascade="all, delete-orphan")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")


class SurveyAssignment(TimestampMixin, Base):
    __tablename__ = "survey_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus, name="assignment_status"),
        default=AssignmentStatus.PENDING,
        nullable=False,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    survey = relationship("Survey", back_populates="assignments")
    user = relationship("User", back_populates="survey_assignments")
