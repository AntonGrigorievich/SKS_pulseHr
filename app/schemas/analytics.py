from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel


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


class SurveyAnalytics(BaseModel):
    survey_id: UUID
    completion_rate: float
    response_rate: float
    enps: float | None
    department_analytics: list[MetricPoint]
    timeline: list[TimelinePoint]

