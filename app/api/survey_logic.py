from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import HRUser
from app.db.session import AsyncSessionDep
from app.schemas.survey_logic import SurveyRuleCreate, SurveyRuleRead, SurveyRuleUpdate
from app.services.survey_logic_service import SurveyLogicService, get_survey_logic_service

router = APIRouter(tags=["survey_logic"])


@router.post("/surveys/{survey_id}/rules", response_model=SurveyRuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(
    survey_id: UUID,
    payload: SurveyRuleCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyLogicService = Depends(get_survey_logic_service),
):
    return await service.create(session, survey_id, payload)


@router.patch("/rules/{rule_id}", response_model=SurveyRuleRead)
async def update_rule(
    rule_id: UUID,
    payload: SurveyRuleUpdate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyLogicService = Depends(get_survey_logic_service),
):
    return await service.update(session, rule_id, payload)


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyLogicService = Depends(get_survey_logic_service),
) -> None:
    await service.delete(session, rule_id)

