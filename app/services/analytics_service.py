from __future__ import annotations

from collections import Counter, defaultdict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import DeliveryStatus, NotificationDelivery
from app.models.question import Question
from app.models.response import Answer, ResponseStatus, SurveyResponse
from app.models.survey import AssignmentStatus, Survey, SurveyAssignment, SurveyStatus
from app.models.user import User


class AnalyticsService:
    async def overview(self, session: AsyncSession) -> dict:
        active_surveys = await session.scalar(
            select(func.count()).select_from(Survey).where(Survey.status == SurveyStatus.PUBLISHED)
        )
        completion_rate = await self._global_completion_rate(session)
        response_rate = await self._global_response_rate(session)
        enps = await self._enps(session)
        latest = await self._latest_responses(session)
        notification_efficiency = await self.notification_efficiency(session)
        return {
            "active_surveys": active_surveys or 0,
            "completion_rate": completion_rate,
            "response_rate": response_rate,
            "enps": enps,
            "latest_responses": latest,
            "notification_efficiency": notification_efficiency,
        }

    async def survey(self, session: AsyncSession, survey_id: UUID) -> dict:
        return {
            "survey_id": survey_id,
            "completion_rate": await self._survey_completion_rate(session, survey_id),
            "response_rate": await self._survey_response_rate(session, survey_id),
            "enps": await self._enps(session, survey_id),
            "department_analytics": await self.department_analytics(session, survey_id),
            "timeline": await self.timeline(session, survey_id),
        }

    async def department_analytics(self, session: AsyncSession, survey_id: UUID) -> list[dict]:
        result = await session.execute(
            select(User.department, func.count(SurveyResponse.id))
            .join(SurveyResponse, SurveyResponse.user_id == User.id)
            .where(SurveyResponse.survey_id == survey_id, SurveyResponse.status == ResponseStatus.SUBMITTED)
            .group_by(User.department)
        )
        return [{"label": department or "Unknown", "value": float(count)} for department, count in result.all()]

    async def timeline(self, session: AsyncSession, survey_id: UUID) -> list[dict]:
        result = await session.execute(
            select(func.date(SurveyResponse.submitted_at), func.count(SurveyResponse.id))
            .where(SurveyResponse.survey_id == survey_id, SurveyResponse.status == ResponseStatus.SUBMITTED)
            .group_by(func.date(SurveyResponse.submitted_at))
            .order_by(func.date(SurveyResponse.submitted_at))
        )
        return [{"date": day, "responses": count} for day, count in result.all()]

    async def notification_efficiency(self, session: AsyncSession) -> dict:
        result = await session.execute(
            select(NotificationDelivery.channel, NotificationDelivery.status, func.count(NotificationDelivery.id))
            .group_by(NotificationDelivery.channel, NotificationDelivery.status)
        )
        data: dict[str, Counter] = defaultdict(Counter)
        for channel, delivery_status, count in result.all():
            data[channel.value][delivery_status.value] = count
        return {
            channel: {
                "sent": counts[DeliveryStatus.SENT.value],
                "failed": counts[DeliveryStatus.FAILED.value],
                "pending": counts[DeliveryStatus.PENDING.value],
            }
            for channel, counts in data.items()
        }

    async def _global_completion_rate(self, session: AsyncSession) -> float:
        total = await session.scalar(select(func.count()).select_from(SurveyAssignment))
        submitted = await session.scalar(
            select(func.count()).select_from(SurveyAssignment).where(SurveyAssignment.status == AssignmentStatus.SUBMITTED)
        )
        return round(((submitted or 0) / total) * 100, 2) if total else 0.0

    async def _global_response_rate(self, session: AsyncSession) -> float:
        total = await session.scalar(select(func.count()).select_from(SurveyResponse))
        submitted = await session.scalar(
            select(func.count()).select_from(SurveyResponse).where(SurveyResponse.status == ResponseStatus.SUBMITTED)
        )
        return round(((submitted or 0) / total) * 100, 2) if total else 0.0

    async def _survey_completion_rate(self, session: AsyncSession, survey_id: UUID) -> float:
        total = await session.scalar(
            select(func.count()).select_from(SurveyAssignment).where(SurveyAssignment.survey_id == survey_id)
        )
        submitted = await session.scalar(
            select(func.count())
            .select_from(SurveyAssignment)
            .where(SurveyAssignment.survey_id == survey_id, SurveyAssignment.status == AssignmentStatus.SUBMITTED)
        )
        return round(((submitted or 0) / total) * 100, 2) if total else 0.0

    async def _survey_response_rate(self, session: AsyncSession, survey_id: UUID) -> float:
        total = await session.scalar(
            select(func.count()).select_from(SurveyResponse).where(SurveyResponse.survey_id == survey_id)
        )
        submitted = await session.scalar(
            select(func.count())
            .select_from(SurveyResponse)
            .where(SurveyResponse.survey_id == survey_id, SurveyResponse.status == ResponseStatus.SUBMITTED)
        )
        return round(((submitted or 0) / total) * 100, 2) if total else 0.0

    async def _enps(self, session: AsyncSession, survey_id: UUID | None = None) -> float | None:
        stmt = (
            select(Answer.value)
            .join(Question, Question.id == Answer.question_id)
            .join(SurveyResponse, SurveyResponse.id == Answer.response_id)
            .where(Question.settings["enps"].as_boolean().is_(True), SurveyResponse.status == ResponseStatus.SUBMITTED)
        )
        if survey_id is not None:
            stmt = stmt.where(SurveyResponse.survey_id == survey_id)
        result = await session.execute(stmt)
        scores = []
        for (value,) in result.all():
            score = value.get("score") if isinstance(value, dict) else None
            if isinstance(score, (int, float)):
                scores.append(score)
        if not scores:
            return None
        promoters = sum(1 for score in scores if score >= 9)
        detractors = sum(1 for score in scores if score <= 6)
        return round(((promoters - detractors) / len(scores)) * 100, 2)

    async def _latest_responses(self, session: AsyncSession) -> list[dict]:
        result = await session.execute(
            select(SurveyResponse, Survey.title)
            .join(Survey, Survey.id == SurveyResponse.survey_id)
            .where(SurveyResponse.status == ResponseStatus.SUBMITTED)
            .order_by(SurveyResponse.submitted_at.desc())
            .limit(10)
        )
        return [
            {
                "response_id": response.id,
                "survey_id": response.survey_id,
                "survey_title": title,
                "submitted_at": response.submitted_at,
                "anonymous": response.user_id is None,
            }
            for response, title in result.all()
        ]


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()
