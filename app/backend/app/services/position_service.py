from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.candidate_position import CandidatePosition
from app.models.enums import PositionStatus
from app.models.position import Position
from app.models.team import Team
from app.models.user import User


async def list_positions(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 20,
    status: str | None = None,
    team_id: int | None = None,
) -> tuple[list[dict], int]:
    count_stmt = (
        select(func.count())
        .select_from(Position)
        .where(Position.is_archived.is_(False))
    )
    if status is not None:
        count_stmt = count_stmt.where(Position.status == status)
    if team_id is not None:
        count_stmt = count_stmt.where(Position.team_id == team_id)

    count_result = await session.exec(count_stmt)
    total_count = count_result.one()[0]

    stmt = (
        select(
            Position,
            Team.name.label("team_name"),
            User.full_name.label("hiring_manager_name"),
            func.count(CandidatePosition.id).label("candidate_count"),
        )
        .join(Team, Position.team_id == Team.id)
        .join(User, Position.hiring_manager_id == User.id)
        .outerjoin(CandidatePosition, Position.id == CandidatePosition.position_id)
        .where(Position.is_archived.is_(False))
    )
    if status is not None:
        stmt = stmt.where(Position.status == status)
    if team_id is not None:
        stmt = stmt.where(Position.team_id == team_id)

    stmt = (
        stmt.group_by(Position.id, Team.name, User.full_name)
        .order_by(Position.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.exec(stmt)
    rows = result.all()

    items = [
        {
            "id": row.Position.id,
            "title": row.Position.title,
            "team_name": row.team_name,
            "hiring_manager_name": row.hiring_manager_name,
            "status": row.Position.status,
            "candidate_count": row.candidate_count,
        }
        for row in rows
    ]

    return items, total_count


async def create_position(
    session: AsyncSession,
    title: str,
    team_id: int,
    hiring_manager_id: int,
    requirements: str | None = None,
) -> Position:
    team_stmt = select(Team).where(Team.id == team_id)
    team_result = await session.exec(team_stmt)
    team = team_result.one_or_none()

    if not team:
        raise ValueError("Team not found")

    user_stmt = select(User).where(User.id == hiring_manager_id)
    user_result = await session.exec(user_stmt)
    user = user_result.one_or_none()

    if not user:
        raise ValueError("Hiring manager not found")

    position = Position(
        title=title,
        requirements=requirements,
        team_id=team_id,
        hiring_manager_id=hiring_manager_id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)
    return position


async def get_position(session: AsyncSession, position_id: int) -> Position | None:
    position = await session.get(Position, position_id)
    if position is None or position.is_archived:
        return None
    return position


async def get_position_detail(session: AsyncSession, position_id: int) -> dict | None:
    """Fetch position with team, hiring manager, and candidates for detail view."""
    position = await get_position(session, position_id)
    if position is None:
        return None

    team = await session.get(Team, position.team_id)
    hiring_manager = await session.get(User, position.hiring_manager_id)

    from app.models.candidate import Candidate

    candidates_stmt = (
        select(CandidatePosition, Candidate)
        .join(Candidate, CandidatePosition.candidate_id == Candidate.id)
        .where(CandidatePosition.position_id == position_id)
    )
    candidates_result = await session.exec(candidates_stmt)
    candidates_rows = candidates_result.all()

    candidates = [
        {
            "candidate_id": row.Candidate.id,
            "candidate_name": row.Candidate.full_name,
            "candidate_email": row.Candidate.email,
            "stage": row.CandidatePosition.stage,
        }
        for row in candidates_rows
    ]

    return {
        "id": position.id,
        "title": position.title,
        "requirements": position.requirements,
        "status": position.status,
        "team_id": position.team_id,
        "team_name": team.name,
        "hiring_manager_id": position.hiring_manager_id,
        "hiring_manager_name": hiring_manager.full_name,
        "is_archived": position.is_archived,
        "candidates": candidates,
        "created_at": position.created_at.isoformat(),
        "updated_at": position.updated_at.isoformat(),
    }


async def update_position(
    session: AsyncSession,
    position_id: int,
    title: str | None = None,
    requirements: str | None = None,
    team_id: int | None = None,
    hiring_manager_id: int | None = None,
    status: str | None = None,
) -> Position:
    position = await session.get(Position, position_id)
    if position is None or position.is_archived:
        raise ValueError("Position not found")

    if team_id is not None:
        team_stmt = select(Team).where(Team.id == team_id)
        team_result = await session.exec(team_stmt)
        team = team_result.one_or_none()
        if not team:
            raise ValueError("Team not found")

    if hiring_manager_id is not None:
        user_stmt = select(User).where(User.id == hiring_manager_id)
        user_result = await session.exec(user_stmt)
        user = user_result.one_or_none()
        if not user:
            raise ValueError("Hiring manager not found")

    if status is not None:
        try:
            PositionStatus(status)
        except ValueError:
            raise ValueError(f"Invalid status: {status}") from None

    if title is not None:
        position.title = title
    if requirements is not None:
        position.requirements = requirements
    if team_id is not None:
        position.team_id = team_id
    if hiring_manager_id is not None:
        position.hiring_manager_id = hiring_manager_id
    if status is not None:
        position.status = status

    session.add(position)
    await session.commit()
    await session.refresh(position)
    return position


async def archive_position(session: AsyncSession, position_id: int) -> Position:
    position = await session.get(Position, position_id)
    if position is None or position.is_archived:
        raise ValueError("Position not found")
    position.is_archived = True
    session.add(position)
    await session.commit()
    await session.refresh(position)
    return position
