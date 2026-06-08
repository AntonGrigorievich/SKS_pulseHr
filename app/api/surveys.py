from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import EmployeeUser, HRUser
from app.db.session import AsyncSessionDep
from app.schemas.survey import (
    EmployeeDashboard,
    EmployeeSurveyCard,
    SurveyAssignmentCreate,
    SurveyAssignmentRead,
    SurveyCreate,
    SurveyDetail,
    SurveyRead,
    SurveyUpdate,
)
from app.services.survey_service import SurveyService, get_survey_service

router = APIRouter(tags=["surveys"])


@router.post("/surveys", response_model=SurveyRead, status_code=status.HTTP_201_CREATED)
async def create_survey(
    payload: SurveyCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.create(session, payload, current_user)


@router.get("/surveys", response_model=list[SurveyRead])
async def list_surveys(
    session: AsyncSessionDep,
    current_user: HRUser,
    limit: int = 100,
    offset: int = 0,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.list(session, limit=limit, offset=offset)


@router.get("/surveys/{survey_id}", response_model=SurveyDetail)
async def get_survey(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.get(session, survey_id)


@router.patch("/surveys/{survey_id}", response_model=SurveyRead)
async def update_survey(
    survey_id: UUID,
    payload: SurveyUpdate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.update(session, survey_id, payload)


@router.post("/surveys/{survey_id}/publish", response_model=SurveyRead)
async def publish_survey(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.publish(session, survey_id)


@router.post("/surveys/{survey_id}/close", response_model=SurveyRead)
async def close_survey(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.close(session, survey_id)


@router.post("/surveys/{survey_id}/archive", response_model=SurveyRead)
async def archive_survey(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.archive(session, survey_id)


@router.post("/surveys/{survey_id}/assignments", response_model=list[SurveyAssignmentRead])
async def assign_survey(
    survey_id: UUID,
    payload: SurveyAssignmentCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.assign(session, survey_id, payload)


@router.get("/employee/dashboard", response_model=EmployeeDashboard)
async def employee_dashboard(
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.employee_dashboard(session, current_user)


@router.get("/employee/surveys", response_model=list[EmployeeSurveyCard])
async def employee_surveys(
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.employee_surveys(session, current_user)


@router.get("/employee/surveys/{survey_id}", response_model=SurveyDetail)
async def employee_survey_detail(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.get(session, survey_id)

