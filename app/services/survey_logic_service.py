from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey_logic import SurveyRule
from app.repositories.survey_repository import QuestionRepository, SurveyRepository, SurveyRuleRepository
from app.schemas.survey_logic import SurveyRuleCreate, SurveyRuleUpdate


class SurveyLogicService:
    def __init__(
        self,
        survey_repository: SurveyRepository,
        question_repository: QuestionRepository,
        rule_repository: SurveyRuleRepository,
    ) -> None:
        self.survey_repository = survey_repository
        self.question_repository = question_repository
        self.rule_repository = rule_repository

    async def create(self, session: AsyncSession, survey_id: UUID, payload: SurveyRuleCreate) -> SurveyRule:
        survey = await self.survey_repository.get(session, survey_id)
        question = await self.question_repository.get(session, payload.target_question_id)
        if survey is None or question is None or question.survey_id != survey_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey or target question not found")
        rule = SurveyRule(survey_id=survey_id, **payload.model_dump())
        created = await self.rule_repository.create(session, rule)
        await session.commit()
        return created

    async def update(self, session: AsyncSession, rule_id: UUID, payload: SurveyRuleUpdate) -> SurveyRule:
        rule = await self.rule_repository.get(session, rule_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)
        await session.commit()
        await session.refresh(rule)
        return rule

    async def delete(self, session: AsyncSession, rule_id: UUID) -> None:
        rule = await self.rule_repository.get(session, rule_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
        await session.delete(rule)
        await session.commit()


def get_survey_logic_service() -> SurveyLogicService:
    return SurveyLogicService(SurveyRepository(), QuestionRepository(), SurveyRuleRepository())

