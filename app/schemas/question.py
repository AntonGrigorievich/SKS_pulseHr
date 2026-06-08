from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.question import QuestionType


class QuestionOptionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1, max_length=255)
    position: int = Field(ge=0)


class QuestionOptionRead(QuestionOptionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class QuestionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    type: QuestionType
    position: int = Field(ge=0)
    is_required: bool = True
    position_x: float = 0.0
    position_y: float = 0.0
    is_start_node: bool = False
    settings: dict = Field(default_factory=dict)
    options: list[QuestionOptionCreate] = Field(default_factory=list)


class QuestionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    type: QuestionType | None = None
    position: int | None = Field(default=None, ge=0)
    is_required: bool | None = None
    position_x: float | None = None
    position_y: float | None = None
    is_start_node: bool | None = None
    settings: dict | None = None
    options: list[QuestionOptionCreate] | None = None


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    survey_id: UUID
    title: str
    description: str | None
    type: QuestionType
    position: int
    is_required: bool
    position_x: float
    position_y: float
    is_start_node: bool
    settings: dict
    options: list[QuestionOptionRead] = []
    created_at: datetime
    updated_at: datetime


class QuestionReorderItem(BaseModel):
    id: UUID
    position: int = Field(ge=0)


class QuestionReorderRequest(BaseModel):
    items: list[QuestionReorderItem]
