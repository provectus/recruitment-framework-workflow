from pydantic import BaseModel


class CandidateCreate(BaseModel):
    full_name: str
    email: str


class CandidateResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_archived: bool


class PositionStageItem(BaseModel):
    position_id: int
    position_title: str
    stage: str


class CandidateListItem(BaseModel):
    id: int
    full_name: str
    email: str
    positions: list[PositionStageItem]
    updated_at: str


class PaginatedCandidates(BaseModel):
    items: list[CandidateListItem]
    total: int
    offset: int
    limit: int


class CandidateDetailResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_archived: bool
    positions: list[PositionStageItem]
    created_at: str
    updated_at: str


class CandidateUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None


class CandidatePositionCreate(BaseModel):
    position_id: int


class CandidatePositionResponse(BaseModel):
    id: int
    candidate_id: int
    position_id: int
    stage: str
    created_at: str
    updated_at: str


class StageUpdate(BaseModel):
    stage: str
