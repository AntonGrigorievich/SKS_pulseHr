from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.response import Answer, SurveyResponse


class ResponseRepository:
    async def get(self, session: AsyncSession, response_id: UUID) -> SurveyResponse | None:
        result = await session.execute(
            select(SurveyResponse)
            .where(SurveyResponse.id == response_id)
            .options(selectinload(SurveyResponse.answers), selectinload(SurveyResponse.survey))
        )
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, response: SurveyResponse) -> SurveyResponse:
        session.add(response)
        await session.flush()
        await session.refresh(response)
        return response

    async def get_answer(
        self,
        session: AsyncSession,
        response_id: UUID,
        question_id: UUID,
    ) -> Answer | None:
        result = await session.execute(
            select(Answer).where(Answer.response_id == response_id, Answer.question_id == question_id)
        )
        return result.scalar_one_or_none()

    async def upsert_answer(
        self,
        session: AsyncSession,
        *,
        response_id: UUID,
        question_id: UUID,
        value: dict,
    ) -> Answer:
        answer = await self.get_answer(session, response_id, question_id)
        if answer is None:
            answer = Answer(response_id=response_id, question_id=question_id, value=value)
            session.add(answer)
        else:
            answer.value = value
        await session.flush()
        await session.refresh(answer)
        return answer

