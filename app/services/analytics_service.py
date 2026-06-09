from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.notification import DeliveryStatus, NotificationDelivery
from app.models.question import Question, QuestionType
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
        survey = await self._survey_or_404(session, survey_id)
        submitted_responses = await self._submitted_responses(session, survey_id)
        assigned_count, assignment_submitted_count = await self._assignment_counts(
            session,
            survey_id,
        )
        response_count = await session.scalar(self._response_count_stmt(survey_id=survey_id))
        submitted_count = (
            assignment_submitted_count
            if assigned_count
            else len(submitted_responses)
        )
        questions = sorted(survey.questions, key=lambda item: item.position)
        return {
            "survey_id": survey_id,
            "title": survey.title,
            "is_anonymous": survey.is_anonymous,
            "assigned_count": assigned_count,
            "submitted_count": submitted_count,
            "response_count": int(response_count or 0),
            "completion_rate": await self._survey_completion_rate(session, survey_id),
            "response_rate": await self._survey_response_rate(session, survey_id),
            "enps": await self._enps(session, survey_id),
            "department_analytics": await self.department_analytics(session, survey_id),
            "timeline": await self.timeline(session, survey_id),
            "question_summaries": self._question_summaries(questions, submitted_responses),
            "responses": self._response_rows(survey, questions, submitted_responses),
        }

    async def department_analytics(self, session: AsyncSession, survey_id: UUID) -> list[dict]:
        department_label = case(
            (SurveyResponse.user_id.is_(None), "Anonymous"),
            else_=func.coalesce(User.department, "Unknown"),
        ).label("department")
        result = await session.execute(
            select(department_label, func.count(SurveyResponse.id))
            .select_from(SurveyResponse)
            .outerjoin(User, SurveyResponse.user_id == User.id)
            .where(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.status == ResponseStatus.SUBMITTED,
            )
            .group_by(department_label)
        )
        return [{"label": department, "value": float(count)} for department, count in result.all()]

    async def timeline(self, session: AsyncSession, survey_id: UUID) -> list[dict]:
        result = await session.execute(
            select(func.date(SurveyResponse.submitted_at), func.count(SurveyResponse.id))
            .where(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.status == ResponseStatus.SUBMITTED,
            )
            .group_by(func.date(SurveyResponse.submitted_at))
            .order_by(func.date(SurveyResponse.submitted_at))
        )
        return [{"date": day, "responses": count} for day, count in result.all()]

    async def notification_efficiency(self, session: AsyncSession) -> dict:
        result = await session.execute(
            select(
                NotificationDelivery.channel,
                NotificationDelivery.status,
                func.count(NotificationDelivery.id),
            )
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
        total, submitted = await self._assignment_counts(session)
        return self._percentage(submitted, total)

    async def _global_response_rate(self, session: AsyncSession) -> float:
        return await self._response_rate(session)

    async def _survey_completion_rate(self, session: AsyncSession, survey_id: UUID) -> float:
        total, submitted = await self._assignment_counts(session, survey_id)
        return self._percentage(submitted, total)

    async def _survey_response_rate(self, session: AsyncSession, survey_id: UUID) -> float:
        return await self._response_rate(session, survey_id)

    async def _assignment_counts(
        self,
        session: AsyncSession,
        survey_id: UUID | None = None,
    ) -> tuple[int, int]:
        total_stmt = select(func.count()).select_from(SurveyAssignment)
        submitted_stmt = (
            select(func.count())
            .select_from(SurveyAssignment)
            .where(SurveyAssignment.status == AssignmentStatus.SUBMITTED)
        )
        if survey_id is not None:
            total_stmt = total_stmt.where(SurveyAssignment.survey_id == survey_id)
            submitted_stmt = submitted_stmt.where(SurveyAssignment.survey_id == survey_id)

        total = await session.scalar(total_stmt)
        submitted = await session.scalar(submitted_stmt)
        return int(total or 0), int(submitted or 0)

    async def _response_rate(self, session: AsyncSession, survey_id: UUID | None = None) -> float:
        assigned_total, assigned_submitted = await self._assignment_counts(session, survey_id)
        if assigned_total:
            return self._percentage(assigned_submitted, assigned_total)

        total = await session.scalar(
            self._response_count_stmt(survey_id=survey_id)
        )
        submitted = await session.scalar(
            self._response_count_stmt(survey_id=survey_id, submitted_only=True)
        )
        return self._percentage(int(submitted or 0), int(total or 0))

    @staticmethod
    def _response_count_stmt(survey_id: UUID | None = None, *, submitted_only: bool = False):
        stmt = select(func.count()).select_from(SurveyResponse)
        if survey_id is not None:
            stmt = stmt.where(SurveyResponse.survey_id == survey_id)
        if submitted_only:
            stmt = stmt.where(SurveyResponse.status == ResponseStatus.SUBMITTED)
        return stmt

    @staticmethod
    def _percentage(numerator: int, denominator: int) -> float:
        return round((numerator / denominator) * 100, 2) if denominator else 0.0

    async def _enps(self, session: AsyncSession, survey_id: UUID | None = None) -> float | None:
        stmt = (
            select(Answer.value, Question.settings)
            .join(Question, Question.id == Answer.question_id)
            .join(SurveyResponse, SurveyResponse.id == Answer.response_id)
            .where(SurveyResponse.status == ResponseStatus.SUBMITTED)
        )
        if survey_id is not None:
            stmt = stmt.where(SurveyResponse.survey_id == survey_id)
        result = await session.execute(stmt)
        scores = []
        for value, settings in result.all():
            if not isinstance(settings, dict) or settings.get("enps") is not True:
                continue
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

    @staticmethod
    async def _survey_or_404(session: AsyncSession, survey_id: UUID) -> Survey:
        result = await session.execute(
            select(Survey)
            .where(Survey.id == survey_id)
            .options(selectinload(Survey.questions).selectinload(Question.options))
        )
        survey = result.scalar_one_or_none()
        if survey is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
        return survey

    @staticmethod
    async def _submitted_responses(session: AsyncSession, survey_id: UUID) -> list[SurveyResponse]:
        result = await session.execute(
            select(SurveyResponse)
            .where(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.status == ResponseStatus.SUBMITTED,
            )
            .options(
                selectinload(SurveyResponse.user),
                selectinload(SurveyResponse.answers),
            )
            .order_by(SurveyResponse.submitted_at.desc(), SurveyResponse.created_at.desc())
        )
        return list(result.scalars().unique().all())

    def _question_summaries(
        self,
        questions: list[Question],
        responses: list[SurveyResponse],
    ) -> list[dict]:
        answers_by_question: dict[UUID, list[dict[str, Any]]] = defaultdict(list)
        question_ids = {question.id for question in questions}
        for response in responses:
            for answer in response.answers:
                if answer.question_id in question_ids and isinstance(answer.value, dict):
                    answers_by_question[answer.question_id].append(answer.value)

        summaries = []
        for question in questions:
            values = answers_by_question[question.id]
            summary = {
                "question_id": question.id,
                "title": question.title,
                "type": question.type,
                "position": question.position,
                "answer_count": len(values),
                "skipped_count": max(len(responses) - len(values), 0),
                "choice_counts": [],
                "rating_average": None,
                "rating_min": None,
                "rating_max": None,
                "rating_distribution": [],
                "matrix_rows": [],
                "text_answers": [],
            }

            if question.type == QuestionType.SINGLE_CHOICE:
                summary["choice_counts"] = self._single_choice_counts(question, values)
            elif question.type == QuestionType.MULTIPLE_CHOICE:
                summary["choice_counts"] = self._multiple_choice_counts(question, values)
            elif question.type == QuestionType.RATING:
                scores = self._rating_scores(values)
                if scores:
                    summary["rating_average"] = round(sum(scores) / len(scores), 2)
                    summary["rating_min"] = min(scores)
                    summary["rating_max"] = max(scores)
                    summary["rating_distribution"] = self._rating_distribution(scores)
            elif question.type == QuestionType.MATRIX:
                summary["matrix_rows"] = self._matrix_rows(question, values)
            elif question.type == QuestionType.TEXT:
                summary["text_answers"] = self._text_answers(values)

            summaries.append(summary)
        return summaries

    def _response_rows(
        self,
        survey: Survey,
        questions: list[Question],
        responses: list[SurveyResponse],
    ) -> list[dict]:
        question_by_id = {question.id: question for question in questions}

        rows = []
        for response in responses:
            answers = []
            sorted_answers = sorted(
                response.answers,
                key=lambda item: question_by_id[item.question_id].position
                if item.question_id in question_by_id
                else 10_000,
            )
            for answer in sorted_answers:
                question = question_by_id.get(answer.question_id)
                if question is None:
                    continue
                answers.append(
                    {
                        "question_id": question.id,
                        "question_title": question.title,
                        "question_type": question.type,
                        "value": answer.value,
                        "display_value": self._display_answer(question, answer.value),
                    }
                )

            rows.append(
                {
                    "response_id": response.id,
                    "status": response.status.value,
                    "started_at": response.started_at,
                    "submitted_at": response.submitted_at,
                    "respondent": self._respondent(survey, response),
                    "answers": answers,
                }
            )
        return rows

    def _single_choice_counts(
        self,
        question: Question,
        values: list[dict[str, Any]],
    ) -> list[dict]:
        counter: Counter[str] = Counter()
        for value in values:
            selected = value.get("option")
            if selected is not None:
                counter[str(selected)] += 1
        return self._choice_counts_for_question(question, counter, len(values))

    def _multiple_choice_counts(
        self,
        question: Question,
        values: list[dict[str, Any]],
    ) -> list[dict]:
        counter: Counter[str] = Counter()
        for value in values:
            selected_options = value.get("options")
            if not isinstance(selected_options, list):
                continue
            for selected in selected_options:
                if selected is not None:
                    counter[str(selected)] += 1
        return self._choice_counts_for_question(question, counter, len(values))

    @staticmethod
    def _rating_scores(values: list[dict[str, Any]]) -> list[float]:
        scores = []
        for value in values:
            score = value.get("score")
            if isinstance(score, (int, float)):
                scores.append(float(score))
        return scores

    def _rating_distribution(self, scores: list[float]) -> list[dict]:
        counter: Counter[float] = Counter(scores)
        return [
            {
                "label": self._format_number(score),
                "value": self._format_number(score),
                "count": int(counter[score]),
                "percent": self._percentage(int(counter[score]), len(scores)),
            }
            for score in sorted(counter)
        ]

    def _matrix_rows(
        self,
        question: Question,
        values: list[dict[str, Any]],
    ) -> list[dict]:
        configured_rows = self._string_list(question.settings.get("rows"))
        configured_columns = self._string_list(question.settings.get("columns"))
        rows = list(configured_rows)
        row_counters: dict[str, Counter[str]] = defaultdict(Counter)

        for value in values:
            row_values = value.get("rows")
            if not isinstance(row_values, dict):
                continue
            for row, selected in row_values.items():
                row_label = str(row)
                if row_label not in rows:
                    rows.append(row_label)
                if selected is not None:
                    row_counters[row_label][str(selected)] += 1

        return [
            {
                "row": row,
                "choice_counts": self._choice_counts(
                    [(column, column) for column in configured_columns],
                    row_counters[row],
                    sum(row_counters[row].values()),
                ),
            }
            for row in rows
        ]

    @staticmethod
    def _text_answers(values: list[dict[str, Any]]) -> list[str]:
        answers = []
        for value in values:
            text = value.get("text")
            if isinstance(text, str) and text.strip():
                answers.append(text.strip())
        return answers

    def _choice_counts_for_question(
        self,
        question: Question,
        counter: Counter[str],
        denominator: int,
    ) -> list[dict]:
        ordered_choices = [(option.label, option.value) for option in question.options]
        return self._choice_counts(ordered_choices, counter, denominator)

    def _choice_counts(
        self,
        ordered_choices: list[tuple[str, str]],
        counter: Counter[str],
        denominator: int,
    ) -> list[dict]:
        seen: set[str] = set()
        result = []
        for label, value in ordered_choices:
            value_key = str(value)
            count = int(counter[value_key])
            result.append(
                {
                    "label": str(label),
                    "value": value_key,
                    "count": count,
                    "percent": self._percentage(count, denominator),
                }
            )
            seen.add(value_key)

        for value, count in counter.items():
            if value in seen:
                continue
            result.append(
                {
                    "label": value,
                    "value": value,
                    "count": int(count),
                    "percent": self._percentage(int(count), denominator),
                }
            )
        return result

    @staticmethod
    def _respondent(survey: Survey, response: SurveyResponse) -> dict:
        if survey.is_anonymous:
            return {"anonymous": True, "label": "Anonymous respondent"}

        user = response.user
        if user is None:
            return {"anonymous": False, "label": "Unknown employee"}

        return {
            "anonymous": False,
            "label": user.full_name or user.phone or "Employee",
            "user_id": user.id,
            "full_name": user.full_name,
            "phone": user.phone,
            "department": user.department,
            "position": user.position,
        }

    def _display_answer(self, question: Question, value: dict) -> str:
        if not isinstance(value, dict):
            return ""

        if question.type == QuestionType.SINGLE_CHOICE:
            return self._option_label(question, value.get("option"))
        if question.type == QuestionType.MULTIPLE_CHOICE:
            selected_options = value.get("options")
            if not isinstance(selected_options, list):
                return ""
            labels = [self._option_label(question, selected) for selected in selected_options]
            return ", ".join(label for label in labels if label)
        if question.type == QuestionType.RATING:
            score = value.get("score")
            return self._format_number(score) if isinstance(score, (int, float)) else ""
        if question.type == QuestionType.MATRIX:
            return self._display_matrix_answer(question, value)
        if question.type == QuestionType.TEXT:
            text = value.get("text")
            return text.strip() if isinstance(text, str) else ""
        return ""

    @staticmethod
    def _option_label(question: Question, selected: Any) -> str:
        if selected is None:
            return ""
        selected_value = str(selected)
        option = next(
            (item for item in question.options if item.value == selected_value),
            None,
        )
        return option.label if option is not None else selected_value

    @staticmethod
    def _display_matrix_answer(question: Question, value: dict) -> str:
        row_values = value.get("rows")
        if not isinstance(row_values, dict):
            return ""

        rows = AnalyticsService._string_list(question.settings.get("rows"))
        if not rows:
            rows = [str(row) for row in row_values]

        parts = []
        for row in rows:
            if row not in row_values:
                continue
            parts.append(f"{row}: {row_values[row]}")

        known_rows = set(rows)
        for row, selected in row_values.items():
            row_label = str(row)
            if row_label not in known_rows:
                parts.append(f"{row_label}: {selected}")
        return "; ".join(parts)

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if item is not None]

    @staticmethod
    def _format_number(value: int | float) -> str:
        number = float(value)
        return str(int(number)) if number.is_integer() else str(round(number, 2))


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()
