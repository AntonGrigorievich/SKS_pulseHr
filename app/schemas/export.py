from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.export import ExportFormat, ExportStatus


class ExportCreate(BaseModel):
    format: ExportFormat


class ExportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    survey_id: UUID
    requested_by_id: UUID
    format: ExportFormat
    status: ExportStatus
    file_path: str | None
    error_message: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

