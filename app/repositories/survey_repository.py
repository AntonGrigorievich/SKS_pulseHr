from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question import Question, QuestionOption
from app.models.survey import Survey, SurveyAssignment, SurveyStatus
from app.models.survey_logic import SurveyRule


class SurveyRepository:
    async def create(self, session: AsyncSession, survey: Survey) -> Survey:
        session.add(survey)
        await session.flush()
        await session.refresh(survey)
        return survey

    async def get(self, session: AsyncSession, survey_id: UUID, *, with_details: bool = False) -> Survey | None:
        stmt: Select = select(Survey).where(Survey.id == survey_id)
        if with_details:
            stmt = stmt.options(
                selectinload(Survey.questions).selectinload(Question.options),
                selectinload(Survey.rules),
                selectinload(Survey.responses),
            )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, session: AsyncSession, *, limit: int, offset: int) -> list[Survey]:
        result = await session.execute(
            select(Survey).order_by(Survey.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def list_published_for_user(self, session: AsyncSession, user_id: UUID) -> list[Survey]:
        assigned_to_user = exists().where(
            SurveyAssignment.survey_id == Survey.id,
            SurveyAssignment.user_id == user_id,
        )
        has_assignments = exists().where(SurveyAssignment.survey_id == Survey.id)
        result = await session.execute(
            select(Survey)
            .where(
                Survey.status == SurveyStatus.PUBLISHED,
                or_(assigned_to_user, ~has_assignments),
            )
            .options(selectinload(Survey.assignments), selectinload(Survey.questions))
            .order_by(Survey.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def list_rules(self, session: AsyncSession, survey_id: UUID) -> list[SurveyRule]:
        result = await session.execute(
            select(SurveyRule).where(SurveyRule.survey_id == survey_id).order_by(SurveyRule.priority.asc())
        )
        return list(result.scalars().all())


class QuestionRepository:
    async def get(self, session: AsyncSession, question_id: UUID) -> Question | None:
        result = await session.execute(
            select(Question).where(Question.id == question_id).options(selectinload(Question.options))
        )
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, question: Question) -> Question:
        session.add(question)
        await session.flush()
        await session.refresh(question)
        created = await self.get(session, question.id)
        if created is None:
            raise RuntimeError("Created question was not found")
        return created

    async def replace_options(
        self,
        session: AsyncSession,
        question: Question,
        options: list[QuestionOption],
    ) -> None:
        question.options.clear()
        await session.flush()
        question.options.extend(options)


class SurveyRuleRepository:
    async def get(self, session: AsyncSession, rule_id: UUID) -> SurveyRule | None:
        return await session.get(SurveyRule, rule_id)

    async def create(self, session: AsyncSession, rule: SurveyRule) -> SurveyRule:
        session.add(rule)
        await session.flush()
        await session.refresh(rule)
        return rule
