from __future__ import annotations

import csv
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.models.export import ExportFormat, ExportJob, ExportStatus
from app.models.question import Question
from app.models.response import Answer, SurveyResponse
from app.models.survey import Survey
from app.models.user import User
from app.schemas.export import ExportCreate

EXPORT_DIR = Path("exports")


class ExportService:
    async def create(self, session: AsyncSession, survey_id: UUID, payload: ExportCreate, current_user: User) -> ExportJob:
        survey = await session.get(Survey, survey_id)
        if survey is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

        job = ExportJob(
            survey_id=survey_id,
            requested_by_id=current_user.id,
            format=payload.format,
            status=ExportStatus.PENDING,
        )
        session.add(job)
        await session.flush()

        rows = await self._rows(session, survey_id)
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        suffix = "csv" if payload.format == ExportFormat.CSV else "xlsx"
        path = EXPORT_DIR / f"survey_{survey_id}_{job.id}.{suffix}"
        if payload.format == ExportFormat.CSV:
            self._write_csv(path, rows)
        else:
            self._write_xlsx(path, rows)

        job.status = ExportStatus.READY
        job.file_path = str(path)
        job.completed_at = utcnow()
        await session.commit()
        await session.refresh(job)
        return job

    async def get(self, session: AsyncSession, export_id: UUID) -> ExportJob:
        job = await session.get(ExportJob, export_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found")
        return job

    async def _rows(self, session: AsyncSession, survey_id: UUID) -> list[dict]:
        result = await session.execute(
            select(SurveyResponse, Question.title, Answer.value)
            .join(Answer, Answer.response_id == SurveyResponse.id)
            .join(Question, Question.id == Answer.question_id)
            .where(SurveyResponse.survey_id == survey_id)
            .order_by(SurveyResponse.submitted_at.desc().nullslast(), Question.position.asc())
        )
        rows = []
        for response, question_title, value in result.all():
            rows.append(
                {
                    "response_id": str(response.id),
                    "submitted_at": response.submitted_at.isoformat() if response.submitted_at else "",
                    "anonymous_session_id": response.anonymous_session_id or "",
                    "user_id": str(response.user_id) if response.user_id else "",
                    "question": question_title,
                    "answer": value,
                }
            )
        return rows

    @staticmethod
    def _write_csv(path: Path, rows: list[dict]) -> None:
        fieldnames = ["response_id", "submitted_at", "anonymous_session_id", "user_id", "question", "answer"]
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _write_xlsx(path: Path, rows: list[dict]) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Survey Responses"
        fieldnames = ["response_id", "submitted_at", "anonymous_session_id", "user_id", "question", "answer"]
        sheet.append(fieldnames)
        for row in rows:
            sheet.append([str(row[field]) for field in fieldnames])
        workbook.save(path)


def get_export_service() -> ExportService:
    return ExportService()

