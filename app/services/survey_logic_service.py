from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
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
        if survey is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
        await self._ensure_question_in_survey(session, payload.target_question_id, survey_id)
        await self._ensure_condition_questions_in_survey(session, payload.condition, survey_id)
        rule = SurveyRule(survey_id=survey_id, **payload.model_dump())
        created = await self.rule_repository.create(session, rule)
        await session.commit()
        return created

    async def update(self, session: AsyncSession, rule_id: UUID, payload: SurveyRuleUpdate) -> SurveyRule:
        rule = await self.rule_repository.get(session, rule_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

        data = payload.model_dump(exclude_unset=True)
        target_question_id = data.get("target_question_id")
        if target_question_id is not None:
            await self._ensure_question_in_survey(session, target_question_id, rule.survey_id)
        condition = data.get("condition")
        if condition is not None:
            await self._ensure_condition_questions_in_survey(session, condition, rule.survey_id)

        for field, value in data.items():
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

    async def _ensure_question_in_survey(
        self,
        session: AsyncSession,
        question_id: UUID,
        survey_id: UUID,
    ) -> Question:
        question = await self.question_repository.get(session, question_id)
        if question is None or question.survey_id != survey_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found in survey",
            )
        return question

    async def _ensure_condition_questions_in_survey(
        self,
        session: AsyncSession,
        condition: dict[str, Any],
        survey_id: UUID,
    ) -> None:
        for question_id in self._condition_question_ids(condition):
            await self._ensure_question_in_survey(session, question_id, survey_id)

    def _condition_question_ids(self, condition: dict[str, Any]) -> set[UUID]:
        question_ids: set[UUID] = set()

        source_question_id = condition.get("source_question_id")
        if isinstance(source_question_id, UUID):
            question_ids.add(source_question_id)
        elif isinstance(source_question_id, str):
            question_ids.add(self._parse_question_id(source_question_id))

        field = condition.get("field")
        if isinstance(field, str):
            parts = field.split(".")
            if len(parts) >= 3 and parts[0] == "answers":
                question_ids.add(self._parse_question_id(parts[1]))

        nested_conditions = condition.get("conditions")
        if isinstance(nested_conditions, list):
            for nested_condition in nested_conditions:
                if isinstance(nested_condition, dict):
                    question_ids.update(self._condition_question_ids(nested_condition))

        return question_ids

    @staticmethod
    def _parse_question_id(value: str) -> UUID:
        try:
            return UUID(value)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Rule condition references an invalid question",
            ) from exc


def get_survey_logic_service() -> SurveyLogicService:
    return SurveyLogicService(SurveyRepository(), QuestionRepository(), SurveyRuleRepository())
