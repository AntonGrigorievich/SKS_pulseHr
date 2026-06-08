from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.survey import AssignmentStatus, SurveyStatus
from app.schemas.question import QuestionRead
from app.schemas.survey_logic import SurveyRuleRead


class SurveyCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_anonymous: bool = False
    estimated_minutes: int = Field(default=5, ge=1, le=240)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class SurveyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_anonymous: bool | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=240)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class SurveyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    status: SurveyStatus
    is_anonymous: bool
    estimated_minutes: int
    starts_at: datetime | None
    ends_at: datetime | None
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime


class SurveyDetail(SurveyRead):
    questions: list[QuestionRead] = []
    rules: list[SurveyRuleRead] = []


class SurveyAssignmentCreate(BaseModel):
    user_ids: list[UUID] = Field(min_length=1)


class SurveyAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    survey_id: UUID
    user_id: UUID
    status: AssignmentStatus
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EmployeeSurveyCard(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: SurveyStatus
    assignment_status: AssignmentStatus | None = None
    is_anonymous: bool
    anonymity_notice: str
    ends_at: datetime | None
    estimated_minutes: int
    completion_percent: int


class EmployeeDashboard(BaseModel):
    active_surveys: int
    completed_surveys: int
    completion_percent: int
    surveys: list[EmployeeSurveyCard]

