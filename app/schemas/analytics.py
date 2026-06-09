from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.question import QuestionType


class MetricPoint(BaseModel):
    label: str
    value: float


class TimelinePoint(BaseModel):
    date: date
    responses: int


class AnalyticsOverview(BaseModel):
    active_surveys: int
    completion_rate: float
    response_rate: float
    enps: float | None
    latest_responses: list[dict]
    notification_efficiency: dict


class ChoiceAnalytics(BaseModel):
    label: str
    value: str
    count: int
    percent: float


class MatrixRowAnalytics(BaseModel):
    row: str
    choice_counts: list[ChoiceAnalytics]


class QuestionAnalyticsSummary(BaseModel):
    question_id: UUID
    title: str
    type: QuestionType
    position: int
    answer_count: int
    skipped_count: int
    choice_counts: list[ChoiceAnalytics] = Field(default_factory=list)
    rating_average: float | None = None
    rating_min: float | None = None
    rating_max: float | None = None
    rating_distribution: list[ChoiceAnalytics] = Field(default_factory=list)
    matrix_rows: list[MatrixRowAnalytics] = Field(default_factory=list)
    text_answers: list[str] = Field(default_factory=list)


class RespondentAnalytics(BaseModel):
    anonymous: bool
    label: str
    user_id: UUID | None = None
    full_name: str | None = None
    phone: str | None = None
    department: str | None = None
    position: str | None = None


class AnswerAnalytics(BaseModel):
    question_id: UUID
    question_title: str
    question_type: QuestionType
    value: dict
    display_value: str


class SurveyResponseAnalytics(BaseModel):
    response_id: UUID
    status: str
    started_at: datetime
    submitted_at: datetime | None
    respondent: RespondentAnalytics
    answers: list[AnswerAnalytics]


class SurveyAnalytics(BaseModel):
    survey_id: UUID
    title: str
    is_anonymous: bool
    assigned_count: int
    submitted_count: int
    response_count: int
    completion_rate: float
    response_rate: float
    enps: float | None
    department_analytics: list[MetricPoint]
    timeline: list[TimelinePoint]
    question_summaries: list[QuestionAnalyticsSummary]
    responses: list[SurveyResponseAnalytics]
