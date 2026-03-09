from datetime import datetime

from pydantic import BaseModel


class PipelineCount(BaseModel):
    stage: str
    count: int


class RecentCandidate(BaseModel):
    id: int
    full_name: str
    position_title: str | None
    stage: str | None
    updated_at: datetime


class PositionSummary(BaseModel):
    id: int
    title: str
    status: str
    candidate_count: int
    team_name: str


class DashboardStats(BaseModel):
    pipeline_counts: list[PipelineCount]
    total_candidates: int
    total_positions: int
    open_positions: int
    recent_candidates: list[RecentCandidate]
    positions_summary: list[PositionSummary]
