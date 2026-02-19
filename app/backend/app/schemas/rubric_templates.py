from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.rubric_structure import RubricStructure


class RubricTemplateListItem(BaseModel):
    id: int
    name: str
    description: str | None
    category_count: int
    position_count: int
    created_at: datetime


class RubricTemplateListResponse(BaseModel):
    items: list[RubricTemplateListItem]
    total: int


class RubricTemplateCreate(BaseModel):
    name: str
    description: str | None = None
    structure: RubricStructure


class RubricTemplateDetail(BaseModel):
    id: int
    name: str
    description: str | None
    structure: dict[str, Any]
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class RubricTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    structure: RubricStructure | None = None


class RubricTemplateArchiveResponse(BaseModel):
    id: int
    is_archived: bool
    position_count: int
