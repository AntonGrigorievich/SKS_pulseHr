from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question, QuestionOption
from app.models.survey import SurveyStatus
from app.repositories.survey_repository import QuestionRepository, SurveyRepository
from app.schemas.question import QuestionCreate, QuestionReorderRequest, QuestionUpdate


class QuestionService:
    def __init__(self, survey_repository: SurveyRepository, question_repository: QuestionRepository) -> None:
        self.survey_repository = survey_repository
        self.question_repository = question_repository

    async def create(self, session: AsyncSession, survey_id: UUID, payload: QuestionCreate) -> Question:
        survey = await self.survey_repository.get(session, survey_id)
        if survey is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
        if survey.status == SurveyStatus.ARCHIVED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Archived survey cannot be edited")

        data = payload.model_dump(exclude={"options"})
        question = Question(survey_id=survey_id, **data)
        question.options = [QuestionOption(**option.model_dump()) for option in payload.options]
        created = await self.question_repository.create(session, question)
        await session.commit()
        return created

    async def update(self, session: AsyncSession, question_id: UUID, payload: QuestionUpdate) -> Question:
        question = await self.question_repository.get(session, question_id)
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

        data = payload.model_dump(exclude_unset=True, exclude={"options"})
        for field, value in data.items():
            setattr(question, field, value)
        if payload.options is not None:
            await self.question_repository.replace_options(
                session,
                question,
                [QuestionOption(**option.model_dump()) for option in payload.options],
            )
        await session.commit()
        await session.refresh(question)
        return question

    async def delete(self, session: AsyncSession, question_id: UUID) -> None:
        question = await self.question_repository.get(session, question_id)
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        await session.delete(question)
        await session.commit()

    async def reorder(self, session: AsyncSession, survey_id: UUID, payload: QuestionReorderRequest) -> None:
        survey = await self.survey_repository.get(session, survey_id, with_details=True)
        if survey is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
        by_id = {question.id: question for question in survey.questions}
        for item in payload.items:
            if item.id not in by_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in survey")
            by_id[item.id].position = item.position
        await session.commit()


def get_question_service() -> QuestionService:
    return QuestionService(SurveyRepository(), QuestionRepository())

