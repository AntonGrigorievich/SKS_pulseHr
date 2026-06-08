from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import HRUser
from app.db.session import AsyncSessionDep
from app.schemas.question import QuestionCreate, QuestionRead, QuestionReorderRequest, QuestionUpdate
from app.services.question_service import QuestionService, get_question_service

router = APIRouter(tags=["questions"])


@router.post("/surveys/{survey_id}/questions", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
async def create_question(
    survey_id: UUID,
    payload: QuestionCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: QuestionService = Depends(get_question_service),
):
    return await service.create(session, survey_id, payload)


@router.patch("/questions/{question_id}", response_model=QuestionRead)
async def update_question(
    question_id: UUID,
    payload: QuestionUpdate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: QuestionService = Depends(get_question_service),
):
    return await service.update(session, question_id, payload)


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: QuestionService = Depends(get_question_service),
) -> None:
    await service.delete(session, question_id)


@router.post("/surveys/{survey_id}/questions/reorder")
async def reorder_questions(
    survey_id: UUID,
    payload: QuestionReorderRequest,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: QuestionService = Depends(get_question_service),
) -> None:
    await service.reorder(session, survey_id, payload)

