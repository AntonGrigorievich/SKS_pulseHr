from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    RATING = "RATING"
    TEXT = "TEXT"
    MATRIX = "MATRIX"

class Question(TimestampMixin, Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType, name="question_type"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    position_x: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    position_y: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_start_node: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    survey = relationship("Survey", back_populates="questions")
    options = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.position",
        lazy="selectin"
    )
    answers = relationship("Answer", back_populates="question")

class QuestionOption(TimestampMixin, Base):
    __tablename__ = "question_options"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    question = relationship("Question", back_populates="options")
