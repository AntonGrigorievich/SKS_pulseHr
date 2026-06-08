from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RuleAction(str, enum.Enum):
    SHOW_QUESTION = "SHOW_QUESTION"
    HIDE_QUESTION = "HIDE_QUESTION"


class SurveyRule(TimestampMixin, Base):
    __tablename__ = "survey_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    action: Mapped[RuleAction] = mapped_column(Enum(RuleAction, name="rule_action"), nullable=False)
    condition: Mapped[dict] = mapped_column(JSONB, nullable=False)

    survey = relationship("Survey", back_populates="rules")
    target_question = relationship("Question")
