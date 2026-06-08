from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ExportFormat(str, enum.Enum):
    CSV = "CSV"
    XLSX = "XLSX"


class ExportStatus(str, enum.Enum):
    PENDING = "PENDING"
    READY = "READY"
    FAILED = "FAILED"


class ExportJob(TimestampMixin, Base):
    __tablename__ = "export_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    format: Mapped[ExportFormat] = mapped_column(Enum(ExportFormat, name="export_format"), nullable=False)
    status: Mapped[ExportStatus] = mapped_column(
        Enum(ExportStatus, name="export_status"),
        default=ExportStatus.PENDING,
        nullable=False,
    )
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    survey = relationship("Survey")
    requested_by = relationship("User")

