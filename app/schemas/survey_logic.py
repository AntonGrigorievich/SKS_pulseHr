from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.survey_logic import RuleAction


class SurveyRuleCreate(BaseModel):
    target_question_id: UUID
    name: str = Field(min_length=1, max_length=255)
    priority: int = Field(default=100, ge=0)
    action: RuleAction
    condition: dict


class SurveyRuleUpdate(BaseModel):
    target_question_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    priority: int | None = Field(default=None, ge=0)
    action: RuleAction | None = None
    condition: dict | None = None


class SurveyRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    survey_id: UUID
    target_question_id: UUID
    name: str
    priority: int
    action: RuleAction
    condition: dict
    created_at: datetime
    updated_at: datetime

