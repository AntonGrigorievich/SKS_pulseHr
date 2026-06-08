from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.response import ResponseStatus


class StartSurveyResponse(BaseModel):
    response_id: UUID
    survey_id: UUID
    is_anonymous: bool
    anonymous_session_id: str | None
    warning: str


class AnswerUpsert(BaseModel):
    question_id: UUID
    value: dict


class AnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    response_id: UUID
    question_id: UUID
    value: dict
    created_at: datetime
    updated_at: datetime


class SurveyResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    survey_id: UUID
    user_id: UUID | None
    anonymous_session_id: str | None
    status: ResponseStatus
    started_at: datetime
    submitted_at: datetime | None
    answers: list[AnswerRead] = []

