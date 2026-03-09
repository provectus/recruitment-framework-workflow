from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from app.schemas.rubric_structure import RubricStructure


class PositionRubricCreate(BaseModel):
    source: Literal["template", "custom"]
    template_id: int | None = None
    structure: RubricStructure | None = None


class PositionRubricResponse(BaseModel):
    id: int
    position_id: int
    source_template_name: str | None
    version_number: int
    structure: dict[str, Any]
    created_by: str
    created_at: datetime


class PositionRubricUpdate(BaseModel):
    structure: RubricStructure


class PositionRubricVersionItem(BaseModel):
    version_number: int
    created_by: str
    created_at: datetime


class PositionRubricVersionListResponse(BaseModel):
    items: list[PositionRubricVersionItem]


class SaveAsTemplateRequest(BaseModel):
    name: str
    description: str | None = None
