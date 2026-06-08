from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import HRUser
from app.db.session import AsyncSessionDep
from app.schemas.analytics import AnalyticsOverview, MetricPoint, SurveyAnalytics, TimelinePoint
from app.services.analytics_service import AnalyticsService, get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def overview(
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.overview(session)


@router.get("/surveys/{survey_id}", response_model=SurveyAnalytics)
async def survey_analytics(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.survey(session, survey_id)


@router.get("/surveys/{survey_id}/enps", response_model=dict)
async def survey_enps(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    data = await service.survey(session, survey_id)
    return {"survey_id": survey_id, "enps": data["enps"]}


@router.get("/surveys/{survey_id}/departments", response_model=list[MetricPoint])
async def departments(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.department_analytics(session, survey_id)


@router.get("/surveys/{survey_id}/timeline", response_model=list[TimelinePoint])
async def timeline(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.timeline(session, survey_id)


@router.get("/notifications", response_model=dict)
async def notifications(
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.notification_efficiency(session)

