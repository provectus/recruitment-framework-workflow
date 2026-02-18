from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.candidate import Candidate
from app.models.candidate_position import CandidatePosition
from app.models.position import Position
from app.models.team import Team
from app.schemas.dashboard import (
    DashboardStats,
    PipelineCount,
    PositionSummary,
    RecentCandidate,
)


async def get_dashboard_stats(session: AsyncSession) -> DashboardStats:
    pipeline_stmt = (
        select(CandidatePosition.stage, func.count())
        .group_by(CandidatePosition.stage)
    )
    pipeline_result = await session.execute(pipeline_stmt)
    pipeline_counts = [
        PipelineCount(stage=row[0], count=row[1])
        for row in pipeline_result.all()
    ]

    total_candidates_result = await session.execute(
        select(func.count()).select_from(Candidate).where(Candidate.is_archived == False)  # noqa: E712
    )
    total_candidates = total_candidates_result.scalar_one()

    total_positions_result = await session.execute(
        select(func.count()).select_from(Position).where(Position.is_archived == False)  # noqa: E712
    )
    total_positions = total_positions_result.scalar_one()

    open_positions_result = await session.execute(
        select(func.count())
        .select_from(Position)
        .where(Position.is_archived == False, Position.status == "open")  # noqa: E712
    )
    open_positions = open_positions_result.scalar_one()

    recent_stmt = (
        select(
            Candidate.id,
            Candidate.full_name,
            Candidate.created_at.label("candidate_created_at"),
            Position.title.label("position_title"),
            CandidatePosition.stage,
            CandidatePosition.updated_at,
        )
        .select_from(Candidate)
        .outerjoin(CandidatePosition, CandidatePosition.candidate_id == Candidate.id)
        .outerjoin(Position, Position.id == CandidatePosition.position_id)
        .where(Candidate.is_archived == False)  # noqa: E712
        .order_by(CandidatePosition.updated_at.desc().nulls_last(), Candidate.created_at.desc())
        .limit(5)
    )
    recent_result = await session.execute(recent_stmt)
    recent_candidates = [
        RecentCandidate(
            id=row.id,
            full_name=row.full_name,
            position_title=row.position_title,
            stage=row.stage,
            updated_at=row.updated_at or row.candidate_created_at,
        )
        for row in recent_result.all()
    ]

    positions_stmt = (
        select(
            Position.id,
            Position.title,
            Position.status,
            func.count(CandidatePosition.id).label("candidate_count"),
            Team.name.label("team_name"),
        )
        .select_from(Position)
        .join(Team, Team.id == Position.team_id)
        .outerjoin(CandidatePosition, CandidatePosition.position_id == Position.id)
        .where(Position.is_archived == False)  # noqa: E712
        .group_by(Position.id, Position.title, Position.status, Team.name)
        .order_by(func.count(CandidatePosition.id).desc())
        .limit(5)
    )
    positions_result = await session.execute(positions_stmt)
    positions_summary = [
        PositionSummary(
            id=row.id,
            title=row.title,
            status=row.status,
            candidate_count=row.candidate_count,
            team_name=row.team_name,
        )
        for row in positions_result.all()
    ]

    return DashboardStats(
        pipeline_counts=pipeline_counts,
        total_candidates=total_candidates,
        total_positions=total_positions,
        open_positions=open_positions,
        recent_candidates=recent_candidates,
        positions_summary=positions_summary,
    )
