from __future__ import annotations

import secrets
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.models.question import Question
from app.models.response import ResponseStatus, SurveyResponse
from app.models.survey import AssignmentStatus, SurveyAssignment, SurveyStatus
from app.models.survey_logic import RuleAction, SurveyRule
from app.models.user import User
from app.repositories.response_repository import ResponseRepository
from app.repositories.survey_repository import QuestionRepository, SurveyRepository
from app.schemas.response import AnswerUpsert


class ResponseService:
    def __init__(
        self,
        survey_repository: SurveyRepository,
        question_repository: QuestionRepository,
        response_repository: ResponseRepository,
    ) -> None:
        self.survey_repository = survey_repository
        self.question_repository = question_repository
        self.response_repository = response_repository

    async def start(self, session: AsyncSession, survey_id: UUID, current_user: User) -> dict:
        survey = await self.survey_repository.get(session, survey_id, with_details=True)
        if survey is None or survey.status != SurveyStatus.PUBLISHED:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published survey not found")

        anonymous_session_id = secrets.token_urlsafe(32) if survey.is_anonymous else None
        response = SurveyResponse(
            survey_id=survey_id,
            user_id=None if survey.is_anonymous else current_user.id,
            anonymous_session_id=anonymous_session_id,
            status=ResponseStatus.IN_PROGRESS,
            started_at=utcnow(),
        )
        created = await self.response_repository.create(session, response)
        await self._mark_assignment(session, survey_id, current_user.id, AssignmentStatus.STARTED)
        await session.commit()
        return {
            "response_id": created.id,
            "survey_id": survey_id,
            "is_anonymous": survey.is_anonymous,
            "anonymous_session_id": anonymous_session_id,
            "warning": (
                "Этот опрос анонимный. HR не сможет определить автора ответа."
                if survey.is_anonymous
                else "Ваши ответы будут доступны HR."
            ),
        }

    async def upsert_answer(
        self,
        session: AsyncSession,
        response_id: UUID,
        payload: AnswerUpsert,
        current_user: User,
    ):
        response = await self._get_owned_response(session, response_id, current_user)
        if response.status == ResponseStatus.SUBMITTED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Response already submitted")
        question = await self.question_repository.get(session, payload.question_id)
        if question is None or question.survey_id != response.survey_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in survey")
        answer = await self.response_repository.upsert_answer(
            session,
            response_id=response_id,
            question_id=payload.question_id,
            value=payload.value,
        )
        await session.commit()
        return answer

    async def submit(self, session: AsyncSession, response_id: UUID, current_user: User) -> SurveyResponse:
        response = await self._get_owned_response(session, response_id, current_user)
        if response.status == ResponseStatus.SUBMITTED:
            return response

        survey = await self.survey_repository.get(session, response.survey_id, with_details=True)
        answers_by_question_id = {
            str(answer.question_id): answer.value for answer in response.answers
        }
        visible_question_ids = {
            question.id
            for question in visible_questions(
                survey.questions,
                survey.rules,
                answers_by_question_id,
            )
        }
        answered_question_ids = {answer.question_id for answer in response.answers}
        missing = [
            str(question.id)
            for question in survey.questions
            if question.id in visible_question_ids
            and question.is_required
            and question.id not in answered_question_ids
        ]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Required questions are missing", "question_ids": missing},
            )

        response.status = ResponseStatus.SUBMITTED
        response.submitted_at = utcnow()
        await self._mark_assignment(session, response.survey_id, current_user.id, AssignmentStatus.SUBMITTED)
        await session.commit()
        await session.refresh(response)
        return response

    async def get(self, session: AsyncSession, response_id: UUID, current_user: User) -> SurveyResponse:
        return await self._get_owned_response(session, response_id, current_user)

    async def _get_owned_response(
        self,
        session: AsyncSession,
        response_id: UUID,
        current_user: User,
    ) -> SurveyResponse:
        response = await self.response_repository.get(session, response_id)
        if response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
        if response.user_id is not None and response.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Response belongs to another user")
        return response

    @staticmethod
    async def _mark_assignment(
        session: AsyncSession,
        survey_id: UUID,
        user_id: UUID,
        assignment_status: AssignmentStatus,
    ) -> None:
        result = await session.execute(
            select(SurveyAssignment).where(
                SurveyAssignment.survey_id == survey_id,
                SurveyAssignment.user_id == user_id,
            )
        )
        assignment = result.scalar_one_or_none()
        if assignment is None:
            assignment = SurveyAssignment(survey_id=survey_id, user_id=user_id)
            session.add(assignment)
        assignment.status = assignment_status
        if assignment_status == AssignmentStatus.SUBMITTED:
            assignment.submitted_at = utcnow()


def get_response_service() -> ResponseService:
    return ResponseService(SurveyRepository(), QuestionRepository(), ResponseRepository())


def read_path(source: dict[str, Any], path: str) -> Any:
    value: Any = source
    for key in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def compare(actual: Any, operator: str, expected: Any) -> bool:
    if operator == "equals":
        return expected in actual if isinstance(actual, list) else actual == expected
    if operator in {"lte", "gte"}:
        try:
            actual_number = float(actual)
            expected_number = float(expected)
        except (TypeError, ValueError):
            return False
        if operator == "lte":
            return actual_number <= expected_number
        return actual_number >= expected_number
    if operator == "in":
        if isinstance(actual, list) and isinstance(expected, list):
            return any(item in expected for item in actual)
        if isinstance(actual, list):
            return expected in actual
        if isinstance(expected, list):
            return actual in expected
    return False


def evaluate(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    op = condition.get("op")
    if op == "ALWAYS" or condition.get("mode") == "always":
        return True

    conditions = condition.get("conditions")
    if not isinstance(conditions, list):
        conditions = []

    nested_conditions = [item for item in conditions if isinstance(item, dict)]
    if op == "AND":
        return all(evaluate(item, context) for item in nested_conditions)
    if op == "OR":
        return any(evaluate(item, context) for item in nested_conditions)
    if op == "NOT":
        return not evaluate(nested_conditions[0] if nested_conditions else {}, context)

    field = condition.get("field")
    operator = condition.get("operator")
    if not isinstance(field, str) or not isinstance(operator, str):
        return False
    return compare(read_path(context, field), operator, condition.get("value"))


def visible_questions(
    questions: Sequence[Question],
    rules: Sequence[SurveyRule],
    answers: dict[str, dict[str, Any]],
) -> list[Question]:
    hidden: set[UUID] = set()
    explicitly_shown: set[UUID] = set()
    context = {"answers": answers}

    for rule in sorted(rules, key=lambda item: item.priority):
        if not evaluate(rule.condition, context):
            continue
        if rule.action == RuleAction.HIDE_QUESTION:
            hidden.add(rule.target_question_id)
        if rule.action == RuleAction.SHOW_QUESTION:
            explicitly_shown.add(rule.target_question_id)

    visible: list[Question] = []
    for question in sorted(questions, key=lambda item: item.position):
        if question.id in hidden:
            continue
        show_rules = [
            rule
            for rule in rules
            if rule.action == RuleAction.SHOW_QUESTION and rule.target_question_id == question.id
        ]
        if show_rules and question.id not in explicitly_shown:
            continue
        visible.append(question)
    return visible
