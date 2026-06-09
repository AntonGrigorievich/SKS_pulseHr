from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationChannel
from app.models.survey import AssignmentStatus, Survey, SurveyAssignment, SurveyStatus
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.repositories.survey_repository import SurveyRepository
from app.schemas.notification import NotificationCreate
from app.schemas.survey import SurveyAssignmentCreate, SurveyCreate, SurveyUpdate
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


PUBLISH_NOTIFICATION_CHANNELS = [
    NotificationChannel.TELEGRAM,
    NotificationChannel.EMAIL,
    NotificationChannel.SMS,
]


class SurveyService:
    def __init__(
        self,
        repository: SurveyRepository,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.repository = repository
        self.notification_service = (
            notification_service
            if notification_service is not None
            else NotificationService(NotificationRepository())
        )

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
        if survey.status == SurveyStatus.PUBLISHED:
            return survey

        survey.status = SurveyStatus.PUBLISHED
        await self._schedule_publish_notifications(session, survey)
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

    async def _schedule_publish_notifications(
        self,
        session: AsyncSession,
        survey: Survey,
    ) -> None:
        recipient_ids = await self.repository.list_publish_recipient_ids(session, survey.id)
        if not recipient_ids:
            logger.info(
                "Survey %s published without active employee notification recipients",
                survey.id,
            )
            await session.commit()
            return

        await self.notification_service.send(
            session,
            self._publish_notification_payload(survey, recipient_ids),
        )

    @staticmethod
    def _publish_notification_payload(survey: Survey, user_ids: list[UUID]) -> NotificationCreate:
        body_parts = [
            f'A new survey "{survey.title}" is available.',
            f"Estimated time: {survey.estimated_minutes} min.",
        ]
        if survey.description:
            body_parts.insert(1, survey.description)
        if survey.ends_at:
            body_parts.append(f"Deadline: {survey.ends_at.isoformat()}.")

        payload = {
            "type": "SURVEY_PUBLISHED",
            "survey_id": str(survey.id),
        }
        if survey.ends_at:
            payload["ends_at"] = survey.ends_at.isoformat()

        title = f"New survey: {survey.title}"
        if len(title) > 255:
            title = f"{title[:252]}..."

        return NotificationCreate(
            survey_id=survey.id,
            title=title,
            body="\n".join(body_parts),
            user_ids=user_ids,
            channels=PUBLISH_NOTIFICATION_CHANNELS,
            step_delay_seconds=0,
            stop_on_success=False,
            payload=payload,
        )


def get_survey_service() -> SurveyService:
    return SurveyService(SurveyRepository())
