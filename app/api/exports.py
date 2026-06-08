from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.core.dependencies import HRUser
from app.db.session import AsyncSessionDep
from app.models.export import ExportStatus
from app.schemas.export import ExportCreate, ExportJobRead
from app.services.export_service import ExportService, get_export_service

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/surveys/{survey_id}", response_model=ExportJobRead, status_code=status.HTTP_201_CREATED)
async def create_export(
    survey_id: UUID,
    payload: ExportCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: ExportService = Depends(get_export_service),
):
    return await service.create(session, survey_id, payload, current_user)


@router.get("/{export_id}", response_model=ExportJobRead)
async def get_export(
    export_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: ExportService = Depends(get_export_service),
):
    return await service.get(session, export_id)


@router.get("/{export_id}/download")
async def download_export(
    export_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: ExportService = Depends(get_export_service),
):
    job = await service.get(session, export_id)
    if job.status != ExportStatus.READY or job.file_path is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Export is not ready")
    path = Path(job.file_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found")
    return FileResponse(path=path, filename=path.name)

