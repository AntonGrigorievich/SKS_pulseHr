from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ResponseStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"


class SurveyResponse(TimestampMixin, Base):
    __tablename__ = "survey_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    anonymous_session_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    status: Mapped[ResponseStatus] = mapped_column(
        Enum(ResponseStatus, name="response_status"),
        default=ResponseStatus.IN_PROGRESS,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    survey = relationship("Survey", back_populates="responses")
    user = relationship("User", back_populates="survey_responses")
    answers = relationship("Answer", back_populates="response", cascade="all, delete-orphan")


class Answer(TimestampMixin, Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("survey_responses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)

    response = relationship("SurveyResponse", back_populates="answers")
    question = relationship("Question", back_populates="answers")

