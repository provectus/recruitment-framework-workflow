from pydantic import BaseModel


class PositionCreate(BaseModel):
    title: str
    requirements: str | None = None
    team_id: int
    hiring_manager_id: int


class PositionResponse(BaseModel):
    id: int
    title: str
    requirements: str | None
    status: str
    team_id: int
    hiring_manager_id: int
    is_archived: bool


class PositionListItem(BaseModel):
    id: int
    title: str
    team_name: str
    hiring_manager_name: str
    status: str
    candidate_count: int


class PaginatedPositions(BaseModel):
    items: list[PositionListItem]
    total: int
    offset: int
    limit: int


class CandidateStageItem(BaseModel):
    candidate_id: int
    candidate_name: str
    candidate_email: str
    stage: str


class PositionDetailResponse(BaseModel):
    id: int
    title: str
    requirements: str | None
    status: str
    team_id: int
    team_name: str
    hiring_manager_id: int
    hiring_manager_name: str
    is_archived: bool
    candidates: list[CandidateStageItem]
    created_at: str
    updated_at: str


class PositionUpdate(BaseModel):
    title: str | None = None
    requirements: str | None = None
    team_id: int | None = None
    hiring_manager_id: int | None = None
    status: str | None = None
