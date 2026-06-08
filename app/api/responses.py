from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import EmployeeUser
from app.db.session import AsyncSessionDep
from app.schemas.response import AnswerRead, AnswerUpsert, StartSurveyResponse, SurveyResponseRead
from app.services.response_service import ResponseService, get_response_service

router = APIRouter(tags=["responses"])


@router.post("/employee/surveys/{survey_id}/start", response_model=StartSurveyResponse)
async def start_survey(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: ResponseService = Depends(get_response_service),
):
    return await service.start(session, survey_id, current_user)


@router.get("/responses/{response_id}", response_model=SurveyResponseRead)
async def get_response(
    response_id: UUID,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: ResponseService = Depends(get_response_service),
):
    return await service.get(session, response_id, current_user)


@router.post("/responses/{response_id}/answers", response_model=AnswerRead)
async def upsert_answer(
    response_id: UUID,
    payload: AnswerUpsert,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: ResponseService = Depends(get_response_service),
):
    return await service.upsert_answer(session, response_id, payload, current_user)


@router.post("/responses/{response_id}/submit", response_model=SurveyResponseRead)
async def submit_response(
    response_id: UUID,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: ResponseService = Depends(get_response_service),
):
    return await service.submit(session, response_id, current_user)

