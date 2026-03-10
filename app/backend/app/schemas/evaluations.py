from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    step_type: str
    status: str
    version: int
    result: dict[str, Any] | None
    error_message: str | None
    source_document_id: int | None
    rubric_version_id: int | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class EvaluationListResponse(BaseModel):
    items: list[EvaluationResponse]


class EvaluationHistoryResponse(BaseModel):
    step_type: str
    items: list[EvaluationResponse]


class EvaluationStatusEvent(BaseModel):
    evaluation_id: int
    step_type: str
    status: str
