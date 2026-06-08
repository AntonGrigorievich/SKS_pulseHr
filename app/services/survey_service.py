from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey import AssignmentStatus, Survey, SurveyAssignment, SurveyStatus
from app.models.user import User
from app.repositories.survey_repository import SurveyRepository
from app.schemas.survey import SurveyAssignmentCreate, SurveyCreate, SurveyUpdate


class SurveyService:
    def __init__(self, repository: SurveyRepository) -> None:
        self.repository = repository

    async def create(self, session: AsyncSession, payload: SurveyCreate, current_user: User) -> Survey:
        survey = Survey(**payload.model_dump(), created_by_id=current_user.id)
        created = await self.repository.create(session, survey)
        await session.commit()
        return created

    async def list(self, session: AsyncSession, *, limit: int, offset: int) -> list[Survey]:
        return await self.repository.list(session, limit=limit, offset=offset)

    async def get(self, session: AsyncSession, survey_id: UUID) -> Survey:
        survey = await self.repository.get(session, survey_id, with_details=True)
        if survey is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
        return survey

    async def update(self, session: AsyncSession, survey_id: UUID, payload: SurveyUpdate) -> Survey:
        survey = await self.get(session, survey_id)
        if survey.status not in {SurveyStatus.DRAFT, SurveyStatus.PUBLISHED}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Survey cannot be edited")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(survey, field, value)
        await session.commit()
        await session.refresh(survey)
        return survey

    async def publish(self, session: AsyncSession, survey_id: UUID) -> Survey:
        survey = await self.get(session, survey_id)
        if not survey.questions:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Survey has no questions")
        survey.status = SurveyStatus.PUBLISHED
        await session.commit()
        await session.refresh(survey)
        return survey

    async def close(self, session: AsyncSession, survey_id: UUID) -> Survey:
        survey = await self.get(session, survey_id)
        survey.status = SurveyStatus.CLOSED
        await session.commit()
        await session.refresh(survey)
        return survey

    async def archive(self, session: AsyncSession, survey_id: UUID) -> Survey:
        survey = await self.get(session, survey_id)
        survey.status = SurveyStatus.ARCHIVED
        await session.commit()
        await session.refresh(survey)
        return survey

    async def assign(
        self,
        session: AsyncSession,
        survey_id: UUID,
        payload: SurveyAssignmentCreate,
    ) -> list[SurveyAssignment]:
        await self.get(session, survey_id)
        existing_result = await session.execute(
            select(SurveyAssignment).where(
                SurveyAssignment.survey_id == survey_id,
                SurveyAssignment.user_id.in_(payload.user_ids),
            )
        )
        existing_user_ids = {assignment.user_id for assignment in existing_result.scalars().all()}
        assignments = [
            SurveyAssignment(survey_id=survey_id, user_id=user_id, status=AssignmentStatus.PENDING)
            for user_id in payload.user_ids
            if user_id not in existing_user_ids
        ]
        session.add_all(assignments)
        await session.commit()
        return assignments

    async def employee_dashboard(self, session: AsyncSession, current_user: User):
        surveys = await self.repository.list_published_for_user(session, current_user.id)
        cards = [self._employee_card(survey, current_user.id) for survey in surveys]
        completed = sum(1 for card in cards if card["completion_percent"] == 100)
        completion_percent = round((completed / len(cards)) * 100) if cards else 0
        return {
            "active_surveys": len(cards) - completed,
            "completed_surveys": completed,
            "completion_percent": completion_percent,
            "surveys": cards,
        }

    async def employee_surveys(self, session: AsyncSession, current_user: User):
        surveys = await self.repository.list_published_for_user(session, current_user.id)
        return [self._employee_card(survey, current_user.id) for survey in surveys]

    @staticmethod
    def _employee_card(survey: Survey, user_id: UUID) -> dict:
        assignment = next((item for item in survey.assignments if item.user_id == user_id), None)
        completion_percent = 100 if assignment and assignment.status == AssignmentStatus.SUBMITTED else 0
        return {
            "id": survey.id,
            "title": survey.title,
            "description": survey.description,
            "status": survey.status,
            "assignment_status": assignment.status if assignment else None,
            "is_anonymous": survey.is_anonymous,
            "anonymity_notice": (
                "Этот опрос анонимный. HR не сможет определить автора ответа."
                if survey.is_anonymous
                else "Ваши ответы будут доступны HR."
            ),
            "ends_at": survey.ends_at,
            "estimated_minutes": survey.estimated_minutes,
            "completion_percent": completion_percent,
        }


def get_survey_service() -> SurveyService:
    return SurveyService(SurveyRepository())

